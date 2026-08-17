# Movie Recommender — Streamlit removed

This version keeps the original FastAPI + TF-IDF + TMDB architecture and replaces the Streamlit UI with a normal HTML/CSS/JavaScript frontend.

## Included features
- Netflix-style home page with Trending, Popular, Top Rated, Now Playing and Upcoming rows
- TMDB search + suggestions
- Movie details with poster/backdrop
- Trailer button
- TF-IDF + cosine-similarity recommendations
- Genre recommendations
- Login / signup with bcrypt
- My List / favorites
- Ratings and written reviews
- Admin dashboard with users, review/favorite counts and feedback moderation
- Existing `movie_rec.db` and original TF-IDF pickle files are preserved

## Project structure
```text
main.py
 database.py
 movie_rec.db
 model/
   df.pkl
   indices.pkl
   tfidf.pkl
   tfidf_matrix.pkl
 frontend/
   index.html
 static/
   css/style.css
   js/app.js
 requirements.txt
 .env.example
```

## Important: copy your existing `.env`
The original ZIP contained a `.env` with your TMDB API key. For security, this converted ZIP does NOT include that secret.

Copy the `.env` file from your old project into this new project folder, or create a new `.env` using `.env.example`:

```env
TMDB_API_KEY=your_key
SESSION_SECRET=some_random_long_value
ADMIN_EMAIL=admin@gmail.com
```

## Run on Windows

Open this folder in VS Code and run:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Open:

`http://127.0.0.1:8000`

Do NOT run Streamlit. There is no Streamlit dependency in this version.

## Existing account/database
The original `movie_rec.db` is included, so existing users, favorites and feedback are retained. If you change the database schema later, keep a backup first.
