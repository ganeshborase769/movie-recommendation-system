import os, pickle, asyncio, socket

from pathlib import Path

from typing import Optional, List, Dict, Any



# ---------------------------------------------------------------------------

# Force IPv4-only DNS resolution.

#

# On many Windows machines, api.themoviedb.org resolves to both an IPv6 and

# an IPv4 address. If the system's IPv6 route is broken/slow (very common on

# home routers/ISPs that "support" IPv6 badly), httpx tries the IPv6 address

# first, stalls, and only then falls back -- which shows up as exactly the

# symptom you're seeing: works sometimes, ConnectError other times, with no

# clear pattern. Forcing IPv4-only resolution removes that flakiness.

# ---------------------------------------------------------------------------

_original_getaddrinfo = socket.getaddrinfo

def _ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):

    return _original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

socket.getaddrinfo = _ipv4_only_getaddrinfo



import bcrypt

import httpx

import numpy as np

import pandas as pd

from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Query, Request

from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import FileResponse

from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel, Field

from starlette.middleware.sessions import SessionMiddleware



from database import *



BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / '.env')

TMDB_API_KEY = os.getenv('TMDB_API_KEY')

TMDB_BASE = 'https://api.themoviedb.org/3'

TMDB_IMG_500 = 'https://image.tmdb.org/t/p/w500'

SESSION_SECRET = os.getenv("SESSION_SECRET", "").strip()
if not SESSION_SECRET or SESSION_SECRET == "replace_with_a_random_secret":
    SESSION_SECRET = os.urandom(32).hex()
    print("WARNING: SESSION_SECRET is not configured; sessions will reset after restart.")

ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@gmail.com').lower().strip()



app = FastAPI(title='Movie Recommender API', version='4.1')

app.add_middleware(

    SessionMiddleware,

    secret_key=SESSION_SECRET,

    max_age=None,

    same_site='lax'

)

app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

app.mount('/static', StaticFiles(directory=str(BASE_DIR / 'static')), name='static')



class TMDBMovieCard(BaseModel):

    tmdb_id: int; title: str; poster_url: Optional[str] = None; release_date: Optional[str] = None; vote_average: Optional[float] = None

class TMDBMovieDetails(BaseModel):

    tmdb_id: int; title: str; overview: Optional[str] = None; release_date: Optional[str] = None; poster_url: Optional[str] = None; backdrop_url: Optional[str] = None; genres: List[dict] = []

class TFIDFRecItem(BaseModel):

    title: str; score: float; tmdb: Optional[TMDBMovieCard] = None

class SearchBundleResponse(BaseModel):

    query: str; movie_details: TMDBMovieDetails; tfidf_recommendations: List[TFIDFRecItem]; genre_recommendations: List[TMDBMovieCard]

class SignupBody(BaseModel): username: str = Field(min_length=3, max_length=40); email: str; password: str = Field(min_length=6)

class LoginBody(BaseModel): email: str; password: str

class FeedbackBody(BaseModel): movie_id: Optional[int] = None; movie_name: str; rating: int = Field(ge=1, le=5); comment: str = ''

class FavoriteBody(BaseModel): movie_id: int; movie_name: str; poster: Optional[str] = None



# ML resources

with open(BASE_DIR / 'model/df.pkl', 'rb') as f: df = pickle.load(f)

with open(BASE_DIR / 'model/indices.pkl', 'rb') as f: indices_obj = pickle.load(f)

with open(BASE_DIR / 'model/tfidf_matrix.pkl', 'rb') as f: tfidf_matrix = pickle.load(f)

with open(BASE_DIR / 'model/tfidf.pkl', 'rb') as f: tfidf_obj = pickle.load(f)

TITLE_TO_IDX = {str(k).strip().lower(): int(v) for k, v in indices_obj.items()}



@app.get('/')

def root(): return FileResponse(BASE_DIR / 'frontend/index.html')

@app.get('/health')

def health(): return {'status': 'ok', 'tmdb_configured': bool(TMDB_API_KEY), 'movies': len(df)}



# ---------------------------------------------------------------------------

# Shared HTTP client (ROOT CAUSE FIX)

#

# The old code opened a brand-new httpx.AsyncClient -- i.e. a brand-new

# TCP + TLS handshake to TMDB -- for EVERY single call. One /movie/search

# request fans out into: 1 search + 1 details + up to \`tfidf_top_n\` attach()

# lookups + 1 genre discover = 10-15 fresh HTTPS connections opened

# back-to-back in a few hundred milliseconds. On Windows, behind

# antivirus/corporate proxies, that burst pattern is exactly what makes TLS

# handshakes fail intermittently ("works sometimes"). An even older version

# of this file shelled out to curl.exe for the same calls, which is where

# the "TMDB curl connection failed. exit code: 35" message came from -- exit

# code 35 is curl's own SSL-connect-error code. That subprocess path is

# already gone (this file only uses httpx), but the underlying fragility

# (many fresh connections, no retries) was still there. Fix: one pooled,

# reused AsyncClient for the whole app + small retry-with-backoff on

# transient connection errors.

# ---------------------------------------------------------------------------

http_client: Optional[httpx.AsyncClient] = None



@app.on_event('startup')

async def _startup_http_client():

    global http_client

    http_client = httpx.AsyncClient(

        timeout=httpx.Timeout(30.0, connect=15.0),

        verify=False,  # some Windows / antivirus / corporate networks break TLS verification for TMDB

        http2=False,

        headers={'User-Agent': 'Mozilla/5.0'},

        limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),

    )



@app.on_event('shutdown')

async def _shutdown_http_client():

    if http_client is not None:

        await http_client.aclose()



async def tmdb_get(path: str, params: Dict[str, Any], retries: int = 5):

    if not TMDB_API_KEY:

        raise HTTPException(status_code=500, detail="TMDB_API_KEY is missing. Add it to .env")

    if http_client is None:

        raise HTTPException(status_code=500, detail="HTTP client is not ready yet, try again in a moment.")



    q = dict(params)

    q['api_key'] = TMDB_API_KEY



    last_error: Optional[Exception] = None

    for attempt in range(1, retries + 1):

        try:

            response = await http_client.get(TMDB_BASE + path, params=q)

        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.RemoteProtocolError) as e:

            last_error = e

            if attempt < retries:

                await asyncio.sleep(0.6 * attempt)  # small backoff, then retry the same call

                continue

            raise HTTPException(status_code=502, detail=f"TMDB connection failed after {retries} attempts: {type(e).__name__}: {e}")

        except Exception as e:

            raise HTTPException(status_code=502, detail=f"TMDB request failed: {type(e).__name__}: {e}")



        if response.status_code != 200:

            raise HTTPException(status_code=502, detail=f"TMDB error {response.status_code}: {response.text[:300]}")



        data = response.json()

        if isinstance(data, dict) and data.get('status_code'):

            raise HTTPException(status_code=502, detail=f"TMDB error: {data.get('status_message', 'Unknown error')}")

        return data



    raise HTTPException(status_code=502, detail=f"TMDB request failed: {last_error}")



def make_img_url(path): return f'{TMDB_IMG_500}{path}' if path else None

async def cards(results, limit=20):

    return [TMDBMovieCard(tmdb_id=int(m['id']), title=m.get('title') or m.get('name') or '', poster_url=make_img_url(m.get('poster_path')), release_date=m.get('release_date'), vote_average=m.get('vote_average')) for m in (results or [])[:limit]]

async def movie_details(mid: int):

    d = await tmdb_get(f'/movie/{mid}', {'language': 'en-US'})

    return TMDBMovieDetails(tmdb_id=int(d['id']), title=d.get('title') or '', overview=d.get('overview'), release_date=d.get('release_date'), poster_url=make_img_url(d.get('poster_path')), backdrop_url=f'https://image.tmdb.org/t/p/original{d.get("backdrop_path")}' if d.get('backdrop_path') else None, genres=d.get('genres', []) or [])

async def tmdb_search(q, page=1): return await tmdb_get('/search/movie', {'query': q, 'include_adult': 'false', 'language': 'en-US', 'page': page})

async def tmdb_first(q):

    r = await tmdb_search(q); return (r.get('results') or [None])[0]



def local_idx(title):

    k = title.strip().lower()

    if k in TITLE_TO_IDX: return TITLE_TO_IDX[k]

    m = df[df['title'].fillna('').str.lower().str.contains(k, regex=False, na=False)]

    if not m.empty: return int(m.index[0])

    raise HTTPException(404, f"Title not found in local dataset: '{title}'")

def tfidf_recs(title, top_n=12):

    idx = local_idx(title); q = tfidf_matrix[idx]; scores = (tfidf_matrix @ q.T).toarray().ravel(); order = np.argsort(-scores); out = []

    for i in order:

        if int(i) == idx: continue

        out.append((str(df.iloc[int(i)]['title']), float(scores[int(i)])))

        if len(out) >= top_n: break

    return out



# Small in-memory cache so the same title isn't looked up on TMDB twice

# within the process lifetime (recommendations often repeat across searches).

_tmdb_title_cache: Dict[str, Optional[dict]] = {}



async def attach(title):

    key = title.strip().lower()

    try:

        if key in _tmdb_title_cache:

            m = _tmdb_title_cache[key]

        else:

            m = await tmdb_first(title)

            _tmdb_title_cache[key] = m

        if not m:

            return None

        return TMDBMovieCard(

            tmdb_id=int(m['id']),

            title=m.get('title') or title,

            poster_url=make_img_url(m.get('poster_path')),

            release_date=m.get('release_date'),

            vote_average=m.get('vote_average')

        )

    except Exception as e:

        print(f"ATTACH ERROR for '{title}': {type(e).__name__}: {e}")

        return None



def current_user(request: Request): return request.session.get('email')

def require_user(request: Request):

    email = current_user(request)

    if not email: raise HTTPException(401, 'Login required')

    return email



def user_payload(email):

    u = get_user(email)

    if not u: return None

    return {'username': u['username'], 'email': u['email'], 'is_admin': u['email'].lower() == ADMIN_EMAIL}



@app.get('/auth/me')

def me(request: Request): return {'logged_in': bool(current_user(request)), 'user': user_payload(current_user(request)) if current_user(request) else None}

@app.post('/auth/signup')

def signup(body: SignupBody, request: Request):

    email = body.email.strip().lower()

    if '@' not in email: raise HTTPException(400, 'Enter a valid email address.')

    if not add_user(body.username.strip(), email, bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()): raise HTTPException(409, 'An account with that email already exists.')

    return {'message': 'Account created successfully.'}

@app.post('/auth/login')

def login(body: LoginBody, request: Request):

    u = get_user(body.email)

    if not u or not bcrypt.checkpw(body.password.encode(), u['password'].encode()): raise HTTPException(401, 'Invalid email or password.')

    request.session['email'] = u['email']; return {'message': 'Login successful', 'user': user_payload(u['email'])}

@app.post('/auth/logout')

def logout(request: Request): request.session.clear(); return {'message': 'Logged out'}



@app.get('/home', response_model=List[TMDBMovieCard])

async def home(category: str = 'popular', limit: int = 24):

    if category == 'trending': d = await tmdb_get('/trending/movie/day', {'language': 'en-US'})

    elif category in {'popular', 'top_rated', 'upcoming', 'now_playing'}: d = await tmdb_get(f'/movie/{category}', {'language': 'en-US', 'page': 1})

    else: raise HTTPException(400, 'Invalid category')

    return await cards(d.get('results', []), limit)

@app.get('/tmdb/search')

async def search(query: str = Query(..., min_length=1), page: int = 1): return await tmdb_search(query, page)

@app.get('/movie/id/{tmdb_id}', response_model=TMDBMovieDetails)

async def details(tmdb_id: int): return await movie_details(tmdb_id)



@app.get('/movie/{tmdb_id}/trailer')

async def trailer(tmdb_id: int):

    try:

        data = await tmdb_get(f'/movie/{tmdb_id}/videos', {'language': 'en-US'})

        videos = data.get('results', [])

        for video in videos:

            if video.get('site') == 'YouTube' and video.get('type') == 'Trailer' and video.get('key'):

                return {'trailer_url': f"https://www.youtube.com/watch?v={video['key']}"}

        for video in videos:

            if video.get('site') == 'YouTube' and video.get('type') == 'Teaser' and video.get('key'):

                return {'trailer_url': f"https://www.youtube.com/watch?v={video['key']}"}

        return {'trailer_url': None}

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(status_code=502, detail=f"Trailer request failed: {type(e).__name__}: {str(e)}")



@app.get('/recommend/genre', response_model=List[TMDBMovieCard])

async def genre(tmdb_id: int, limit: int = 18):

    d = await movie_details(tmdb_id)

    if not d.genres: return []

    x = await tmdb_get('/discover/movie', {'with_genres': d.genres[0]['id'], 'language': 'en-US', 'sort_by': 'popularity.desc', 'page': 1})

    return [c for c in await cards(x.get('results', []), limit) if c.tmdb_id != tmdb_id]

@app.get('/recommend/tfidf')

def rec_tfidf(title: str, top_n: int = 10): return [{'title': t, 'score': s} for t, s in tfidf_recs(title, top_n)]



@app.get('/movie/search', response_model=SearchBundleResponse)

async def bundle(query: str, tfidf_top_n: int = 12, genre_limit: int = 12):

    best = await tmdb_first(query)

    if not best:

        raise HTTPException(404, 'No TMDB movie found for this search.')



    d = await movie_details(int(best['id']))



    try:

        local = tfidf_recs(d.title, tfidf_top_n)

    except Exception:

        try:

            local = tfidf_recs(query, tfidf_top_n)

        except Exception:

            local = []



# Fetch TMDB cards for every local recommendation CONCURRENTLY (bounded

# to 5 at a time) instead of one-by-one. This is both faster and, on top

# of the shared pooled client above, much less likely to trip a

# transient connection error. return_exceptions=True means one bad

# lookup can never crash the whole endpoint.

    sem = asyncio.Semaphore(5)

    async def _attach_bounded(title):

        async with sem:

            return await attach(title)



    tmdb_cards = await asyncio.gather(*[_attach_bounded(t) for t, _ in local], return_exceptions=True)



    recs = []

    for (t, s), card in zip(local, tmdb_cards):

        if isinstance(card, Exception):

            card = None

        recs.append(TFIDFRecItem(title=t, score=s, tmdb=card))



# Genre recommendations are a bonus section -- never let a failure here

# take down a response that otherwise succeeded.

    genres = []

    if d.genres:

        try:

            x = await tmdb_get('/discover/movie', {'with_genres': d.genres[0]['id'], 'language': 'en-US', 'sort_by': 'popularity.desc', 'page': 1})

            genres = [c for c in await cards(x.get('results', []), genre_limit) if c.tmdb_id != d.tmdb_id]

        except Exception as e:

            print(f"GENRE RECS ERROR: {type(e).__name__}: {e}")

            genres = []



    return SearchBundleResponse(query=query, movie_details=d, tfidf_recommendations=recs, genre_recommendations=genres)



@app.get('/favorites')

def favorites(request: Request):

    email = require_user(request); return [dict(x) for x in get_favorites(email)]

@app.post('/favorites')

def favorite_add(body: FavoriteBody, request: Request):

    email = require_user(request); ok = add_favorite(email, body.movie_id, body.movie_name, body.poster); return {'saved': ok}

@app.delete('/favorites/{movie_id}')

def favorite_remove(movie_id: int, request: Request):

    email = require_user(request); remove_favorite(email, movie_id); return {'removed': True}

@app.get('/favorites/{movie_id}/status')

def favorite_status(movie_id: int, request: Request):

    email = require_user(request); return {'favorite': is_favorite(email, movie_id)}



@app.get('/feedback/movie/{movie_name}')

def feedback_movie(movie_name: str):

    avg, total = get_movie_rating_stats(movie_name); return {'average': avg, 'total': total, 'reviews': [dict(x) for x in get_feedback_for_movie(movie_name)]}

@app.post('/feedback')

def feedback(body: FeedbackBody, request: Request):

    email = require_user(request); add_feedback(email, body.movie_name, body.rating, body.comment, body.movie_id); return {'message': 'Feedback submitted'}



@app.get('/admin/stats')

def admin_stats(request: Request):

    email = require_user(request)

    if email.lower() != ADMIN_EMAIL: raise HTTPException(403, 'Admin access required')

    return {'users': get_total_users(), 'reviews': get_total_feedback(), 'favorites': get_total_favorites(), 'average_rating': get_average_platform_rating(), 'top_rated': [dict(x) for x in get_top_rated_movies()], 'most_favorited': [dict(x) for x in get_most_favorited_movies()]}

@app.get('/admin/users')

def admin_users(request: Request):

    email = require_user(request)

    if email.lower() != ADMIN_EMAIL: raise HTTPException(403, 'Admin access required')

    return [dict(x) for x in get_all_users()]

@app.get('/admin/feedback')

def admin_feedback(request: Request):

    email = require_user(request)

    if email.lower() != ADMIN_EMAIL: raise HTTPException(403, 'Admin access required')

    return [dict(x) for x in get_feedback()]

@app.delete('/admin/feedback/{feedback_id}')

def admin_delete_feedback(feedback_id: int, request: Request):

    email = require_user(request)

    if email.lower() != ADMIN_EMAIL: raise HTTPException(403, 'Admin access required')

    delete_feedback(feedback_id); return {'deleted': True}



create_tables()
