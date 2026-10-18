
const app = document.getElementById("app");
const nav = document.getElementById("nav");

let me = null;
let suggestTimer = null;

const NO_POSTER =
  "data:image/svg+xml;charset=UTF-8," +
  encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" width="500" height="750">
      <rect width="100%" height="100%" fill="#101827"/>
      <text x="50%" y="50%" fill="#9aabc6" font-family="sans-serif"
        font-size="26" text-anchor="middle" dominant-baseline="middle">
        No Poster
      </text>
    </svg>
  `);

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  })[c]);

// ======================================================
// API
// ======================================================

async function api(url, opt = {}) {
  const options = {
    credentials: "include",
    ...opt,
    headers: {
      ...(opt.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      ...(opt.headers || {}),
    },
  };

  const response = await fetch(url, options);

  let data = {};

  try {
    data = await response.json();
  } catch {
    // Some endpoints may return an empty response.
  }

  if (!response.ok) {
    throw new Error(
      data.detail || data.message || "Request failed"
    );
  }

  return data;
}

// ======================================================
// TOAST
// ======================================================

function toast(message) {
  const container = document.getElementById("toast");

  if (!container) {
    console.log(message);
    return;
  }

  const item = document.createElement("div");
  item.className = "toast";
  item.textContent = message;

  container.appendChild(item);

  setTimeout(() => item.remove(), 2500);
}

// ======================================================
// NAVIGATION
// ======================================================

function renderNav() {
  if (!nav) return;

  nav.innerHTML = me
    ? `
      <button class="nav-btn" onclick="go('home')">⌂ Home</button>
      <button class="nav-btn" onclick="go('favorites')">♡ My List</button>
      ${
        me.is_admin
          ? `<button class="nav-btn nav-admin" onclick="go('admin')">♜ Admin</button>`
          : ""
      }
      <button class="nav-btn" onclick="logout()">⇥ Logout</button>
    `
    : `
      <button class="nav-btn" onclick="go('login')">Login</button>
      <button class="btn btn-primary" onclick="go('signup')">Sign Up</button>
    `;
}

function go(route, id) {
  location.hash =
    route + (id !== undefined ? "/" + encodeURIComponent(id) : "");
}

function need() {
  if (!me) {
    go("login");
    return false;
  }

  return true;
}

// ======================================================
// INITIALIZATION AND ROUTER
// ======================================================

async function init() {
  try {
    const data = await api("/auth/me");
    me = data.user;
  } catch {
    me = null;
  }

  renderNav();

  const route = location.hash.slice(1).split("/")[0];

  if (!me && route !== "login" && route !== "signup") {
    go("login");
  } else {
    router();
  }
}

window.addEventListener("load", init);
window.addEventListener("hashchange", router);

async function router() {
  const parts = location.hash.slice(1).split("/");
  const route = parts[0];
  const id = decodeURIComponent(parts.slice(1).join("/"));

  if (!route || route === "home") return home();
  if (route === "login") return auth(false);
  if (route === "signup") return auth(true);
  if (route === "favorites") return favorites();
  if (route === "admin") return admin();
  if (route === "movie") return details(id);
  if (route === "movie-search") return movieSearch(id);
}

// ======================================================
// MOVIE CARD
// ======================================================

function card(movie) {
  const id = Number(movie.tmdb_id ?? movie.id);

  return `
    <article class="card movie-card"
      onclick="go('movie', ${Number.isFinite(id) ? id : 0})">

      <img
        class="poster"
        loading="lazy"
        src="${esc(movie.poster_url || movie.poster || NO_POSTER)}"
        onerror="this.onerror=null;this.src='${NO_POSTER}'"
        alt="${esc(movie.title || "Movie poster")}"
      >

      <div class="card-body">
        <h3>${esc(movie.title || movie.movie_name || "Untitled")}</h3>

        <div class="muted">
          ★ ${esc(movie.vote_average ?? "—")}
          ${
            movie.release_date
              ? " • " + esc(movie.release_date.slice(0, 4))
              : ""
          }
        </div>
      </div>
    </article>
  `;
}

// ======================================================
// HOME
// ======================================================



async function home() {
  if (!me) return auth(false);

  app.innerHTML = `
    <main class="wrap home-page">

      <section class="search-section">
        <div class="search-heading">
          <span class="eyebrow">✦ YOUR NEXT MOVIE STARTS HERE</span>
          <h1>Movies you'll <span>love.</span></h1>
          <p>Discover trending hits, hidden gems and your next favorite story.</p>
        </div>

        <div class="search">
          <input
            id="q"
            placeholder="Search movies, actors or titles..."
            autocomplete="off"
            oninput="suggest(this.value)"
            onkeydown="if(event.key==='Enter')searchMovie()"
          >
          <button class="btn btn-primary" onclick="searchMovie()">
            🔍 Search
          </button>
          <div id="suggestions" class="suggestions"></div>
        </div>
      </section>

      <div id="homeRows">
        <div class="home-loading">
          <div class="loading-spinner"></div>
          <p>Preparing your movie experience...</p>
        </div>
      </div>

    </main>
  `;

  const rows = document.getElementById("homeRows");

  const categories = [
    ["trending", "🔥", "Trending Now", "The movies everyone's talking about"],
    ["popular", "🎬", "Popular Movies", "Popular picks worth your time"],
    ["top_rated", "⭐", "Top Rated", "Stories loved by movie fans"],
    ["now_playing", "🍿", "Now Playing", "What's playing right now"],
    ["upcoming", "🚀", "Coming Soon", "Your next watch starts here"]
  ];

  try {
    const firstData = await api("/home?category=trending&limit=18");
    const firstMovies = Array.isArray(firstData)
      ? firstData
      : firstData.results || [];

    const featured = firstMovies[0];

    rows.innerHTML = "";

    
if (featured) {
  const heroImage =
    featured.backdrop_url ||
    featured.backdrop ||
    featured.poster_url ||
    featured.poster ||
    "";

  const heroId = Number(featured.tmdb_id ?? featured.id) || 0;

  rows.insertAdjacentHTML("beforeend", `
    <section class="hero-section">
      <div
        class="hero-banner cinematic-hero"
        style="--hero-image: url('${esc(heroImage)}')"
      >
        <div class="hero-overlay"></div>

        <div class="hero-content">
          <div class="hero-badges">
            <span class="hero-badge">🔥 #1 TRENDING</span>
            <span class="hero-badge hero-rating">
              ★ ${esc(
                Number(featured.vote_average || 0).toFixed(1)
              )}
            </span>
          </div>

          <p class="hero-kicker">FEATURED MOVIE</p>

          <h2>${esc(featured.title || "Featured Movie")}</h2>

          <p class="hero-meta">
            ${featured.release_date
              ? esc(featured.release_date.slice(0, 4)) + " · "
              : ""}
            MOVIE EXPERIENCE
          </p>

          <p class="hero-description">
            ${esc(
              featured.overview ||
              "Discover your next favorite movie."
            )}
          </p>

          <div class="hero-actions">
            <button
              class="btn btn-primary"
              onclick="go('movie', ${heroId})"
            >
              ▶ Explore Movie
            </button>

            <button
              class="hero-secondary"
              onclick="document.getElementById('trending-section')?.scrollIntoView({behavior:'smooth'})"
            >
              Browse Movies ↓
            </button>
          </div>
        </div>

        <div class="hero-poster-box">
          <img
            src="${esc(
              featured.poster_url ||
              featured.poster ||
              NO_POSTER
            )}"
            onerror="this.onerror=null;this.src='${NO_POSTER}'"
            alt="${esc(featured.title || "Movie")} poster"
          >
        </div>
      </div>
    </section>
  `);
}


    for (const [index, [category, icon, title, subtitle]] of categories.entries()) {
      let movies = [];

      if (category === "trending") {
        movies = firstMovies.slice(1);
      } else {
        try {
          const data = await api(
            `/home?category=${encodeURIComponent(category)}&limit=18`
          );
          movies = Array.isArray(data) ? data : data.results || [];
        } catch (error) {
          console.error(`Unable to load ${category}:`, error);
        }
      }

      const sectionId = category === "trending"
        ? "trending-section"
        : `section-${category}`;

      rows.insertAdjacentHTML("beforeend", `
        <section class="movie-shelf" id="${sectionId}">
          <div class="shelf-heading">
            <div class="shelf-title-group">
              <span class="shelf-icon">${icon}</span>
              <div>
                <h2>${title}</h2>
                <p>${subtitle}</p>
              </div>
            </div>
            <span class="shelf-count">
              ${movies.length} MOVIES
            </span>
          </div>

          ${
            movies.length
              ? `<div class="row movie-row">
                  ${movies.map(card).join("")}
                </div>`
              : `<div class="shelf-empty">No movies available right now.</div>`
          }
        </section>
      `);
    }

  } catch (error) {
    rows.innerHTML = `
      <div class="home-error">
        <h2>Oops! Something went wrong.</h2>
        <p>${esc(error.message)}</p>
        <button class="btn btn-primary" onclick="home()">Try Again</button>
      </div>
    `;
  }
}



// ======================================================
// MOVIE SEARCH SUGGESTIONS
// ======================================================

async function suggest(query) {
  clearTimeout(suggestTimer);

  const box = document.getElementById("suggestions");

  if (!box) return;

  if (!query || query.trim().length < 2) {
    box.innerHTML = "";
    return;
  }

  suggestTimer = setTimeout(async () => {
    try {
      const data = await api(
        "/tmdb/search?query=" + encodeURIComponent(query.trim())
      );

      const results = (data.results || []).slice(0, 7);

      box.innerHTML = results
        .map(
          (movie) => `
            <button
              type="button"
              onclick="go('movie', ${Number(movie.id)})"
            >
              <span>${esc(movie.title || movie.name)}</span>
              <span class="suggestion-year">
                ${
                  movie.release_date
                    ? esc(movie.release_date.slice(0, 4))
                    : ""
                }
              </span>
            </button>
          `
        )
        .join("");
    } catch {
      box.innerHTML = "";
    }
  }, 250);
}

function searchMovie() {
  const input = document.getElementById("q");
  const query = input?.value.trim();

  if (query) {
    go("movie-search", query);
  }
}

// ======================================================
// SEARCH RESULTS
// ======================================================

async function movieSearch(query) {
  if (!need()) return;

  app.innerHTML = `
    <div class="wrap loading">Searching movies...</div>
  `;

  try {
    const data = await api(
      "/tmdb/search?query=" + encodeURIComponent(query)
    );

    const results = (data.results || []).slice(0, 24).map((movie) => ({
      tmdb_id: movie.id,
      title: movie.title || movie.name || "",
      poster_url: movie.poster_path
        ? "https://image.tmdb.org/t/p/w500" + movie.poster_path
        : null,
      release_date: movie.release_date || movie.first_air_date,
      vote_average: movie.vote_average,
    }));

    app.innerHTML = `
      <div class="wrap">
        <section class="section">
          <div class="search-results-heading">
            <span class="eyebrow">YOUR SEARCH</span>
            <h1>Results for <span>“${esc(query)}”</span></h1>
            <p>${results.length} movies displayed</p>
          </div>

          <div class="row">
            ${
              results.length
                ? results.map(card).join("")
                : `<div class="empty">No movies found.</div>`
            }
          </div>
        </section>
      </div>
    `;
  } catch (error) {
    app.innerHTML = `
      <div class="wrap empty">${esc(error.message)}</div>
    `;
  }
}

// ======================================================
// MOVIE DETAILS
// ======================================================

async function details(id) {
  if (!need()) return;

  app.innerHTML = `
    <div class="wrap loading">Loading movie details...</div>
  `;

  try {
    const movie = await api("/movie/id/" + encodeURIComponent(id));

    let trailer = {};
    let favorite = { favorite: false };
    let feedback = {};

    try {
      trailer = await api("/movie/" + id + "/trailer");
    } catch {}

    try {
      favorite = await api("/favorites/" + id + "/status");
    } catch {}

    try {
      feedback = await api(
        "/feedback/movie/" + encodeURIComponent(movie.title)
      );
    } catch {}

    const genres = Array.isArray(movie.genres) ? movie.genres : [];
    const reviews = Array.isArray(feedback.reviews)
      ? feedback.reviews
      : [];

    app.innerHTML = `
      <div class="wrap detail">

        <div
          class="backdrop"
          style="background-image:linear-gradient(90deg,rgba(7,11,20,.96),rgba(7,11,20,.45)),url('${esc(movie.backdrop_url || movie.poster_url || "")}')"
        ></div>

        <div class="detail-grid">
          <div>
            <img
              class="detail-poster"
              src="${esc(movie.poster_url || NO_POSTER)}"
              onerror="this.onerror=null;this.src='${NO_POSTER}'"
              alt="${esc(movie.title)}"
            >
          </div>

          <div class="detail-copy">
            <div class="eyebrow">NOW VIEWING</div>

            <h1>${esc(movie.title)}</h1>

            <div>
              ${
                movie.release_date
                  ? `<span class="pill">📅 ${esc(movie.release_date)}</span>`
                  : ""
              }

              ${genres
                .map(
                  (genre) =>
                    `<span class="pill">${esc(genre.name)}</span>`
                )
                .join("")}
            </div>

            <p>${esc(movie.overview || "No overview available.")}</p>

            <div class="actions">
              <button
                class="btn btn-primary"
                onclick="toggleFav(${Number(id)}, ${Boolean(favorite.favorite)})"
              >
                ${favorite.favorite ? "✓ In My List" : "♡ Add to My List"}
              </button>

              ${
                trailer.trailer_url
                  ? `<button class="btn" onclick="window.open('${esc(trailer.trailer_url)}','_blank','noopener')">▶ Watch Trailer</button>`
                  : ""
              }
            </div>
          </div>
        </div>

        <section class="section">
          <h2>⭐ Ratings & Reviews</h2>

          <p class="muted">
            ${
              feedback.average
                ? `★ ${esc(feedback.average)}/5 • ${esc(feedback.total)} reviews`
                : "No reviews yet."
            }
          </p>

          <form class="auth-box review-form"
            onsubmit="submitFeedback(event, ${Number(id)})">

            <h3>Share Your Review</h3>

            <label for="rating">Your rating</label>
            <select id="rating">
              <option value="5">★★★★★ - Excellent</option>
              <option value="4">★★★★☆ - Very Good</option>
              <option value="3">★★★☆☆ - Good</option>
              <option value="2">★★☆☆☆ - Fair</option>
              <option value="1">★☆☆☆☆ - Poor</option>
            </select>

            <label for="comment">Your comments</label>
            <textarea
              id="comment"
              placeholder="What did you think about this movie?"
              rows="4"
            ></textarea>

            <button class="btn btn-primary" type="submit">
              Submit Review
            </button>
          </form>

          ${
            reviews
              .map(
                (review) => `
                  <div class="review">
                    <div class="stars">
                      ${"★".repeat(
                        Math.max(0, Math.min(5, Number(review.rating) || 0))
                      )}
                    </div>
                    <p>${esc(review.comment || "")}</p>
                  </div>
                `
              )
              .join("") || ""
          }
        </section>

        <section class="section" id="recs">
          <h2>Similar Movies</h2>
          <div class="loading">Loading recommendations...</div>
        </section>
      </div>
    `;

    try {
      const recommendations = await api(
        "/movie/search?query=" +
          encodeURIComponent(movie.title) +
          "&tfidf_top_n=12&genre_limit=12"
      );

      const recs = document.getElementById("recs");

      if (recs) {
        const tfidf = (recommendations.tfidf_recommendations || [])
          .map((item) => item.tmdb)
          .filter(Boolean);

        const genre = recommendations.genre_recommendations || [];

        recs.innerHTML = `
          <h2>🔎 Similar Movies</h2>
          <div class="row">${tfidf.map(card).join("")}</div>

          <h2>🎭 More Like This</h2>
          <div class="row">${genre.map(card).join("")}</div>
        `;
      }
    } catch (error) {
      const recs = document.getElementById("recs");
      if (recs) {
        recs.innerHTML = `<p class="muted">Recommendations are unavailable.</p>`;
      }
    }
  } catch (error) {
    app.innerHTML = `
      <div class="wrap empty">
        <h2>Unable to load movie</h2>
        <p>${esc(error.message)}</p>
        <button class="btn" onclick="go('home')">Back to Home</button>
      </div>
    `;
  }
}

// ======================================================
// FAVORITES
// ======================================================

async function toggleFav(id, current) {
  try {
    if (current) {
      await api("/favorites/" + id, { method: "DELETE" });
      toast("Removed from My List");
    } else {
      const movie = await api("/movie/id/" + id);

      await api("/favorites", {
        method: "POST",
        body: JSON.stringify({
          movie_id: id,
          movie_name: movie.title,
          poster: movie.poster_url,
        }),
      });

      toast("Added to My List ❤️");
    }

    details(id);
  } catch (error) {
    toast(error.message);
  }
}

async function favorites() {
  if (!need()) return;

  app.innerHTML = `
    <div class="wrap loading">Loading My List...</div>
  `;

  try {
    const data = await api("/favorites");

    app.innerHTML = `
      <div class="wrap">
        <section class="section">
          <div class="eyebrow">YOUR COLLECTION</div>
          <h1>♡ My List</h1>

          <div class="list">
            ${
              data.length
                ? data
                    .map(
                      (movie) => `
                        <article class="fav-card">
                          <img
                            class="poster"
                            src="${esc(movie.poster || NO_POSTER)}"
                            onerror="this.onerror=null;this.src='${NO_POSTER}'"
                            alt="${esc(movie.movie_name)}"
                          >

                          <div class="card-body">
                            <h3>${esc(movie.movie_name)}</h3>

                            <button class="btn btn-primary"
                              onclick="go('movie',${Number(movie.movie_id)})">
                              View Movie
                            </button>

                            <button class="btn"
                              onclick="removeFav(${Number(movie.movie_id)})">
                              Remove
                            </button>
                          </div>
                        </article>
                      `
                    )
                    .join("")
                : `<div class="empty">
                    <h3>Your list is empty</h3>
                    <p>Add your favorite movies to see them here.</p>
                    <button class="btn btn-primary" onclick="go('home')">
                      Explore Movies
                    </button>
                  </div>`
            }
          </div>
        </section>
      </div>
    `;
  } catch (error) {
    app.innerHTML = `
      <div class="wrap empty">${esc(error.message)}</div>
    `;
  }
}

async function removeFav(id) {
  try {
    await api("/favorites/" + id, { method: "DELETE" });
    toast("Removed from My List");
    favorites();
  } catch (error) {
    toast(error.message);
  }
}

// ======================================================
// REVIEWS
// ======================================================

async function submitFeedback(event, id) {
  event.preventDefault();

  try {
    const movie = await api("/movie/id/" + id);

    await api("/feedback", {
      method: "POST",
      body: JSON.stringify({
        movie_id: id,
        movie_name: movie.title,
        rating: Number(document.getElementById("rating").value),
        comment: document.getElementById("comment").value,
      }),
    });

    toast("Review submitted ⭐");
    details(id);
  } catch (error) {
    toast(error.message);
  }
}

// ======================================================
// LOGIN / SIGNUP
// ======================================================

function auth(signup) {
  app.innerHTML = `
    <div class="auth">
      <div class="auth-box">

        <div class="eyebrow">MOVIE RECOMMENDER</div>

        <h1>${signup ? "Create Account" : "Welcome Back"}</h1>

        <p class="muted">
          ${signup
            ? "Join us and discover your next favorite movie."
            : "Login to continue your movie journey."}
        </p>

        <form onsubmit="submitAuth(event, ${signup})">

          ${
            signup
              ? `<label for="username">Username</label>
                 <input id="username" placeholder="Enter username" required>`
              : ""
          }

          <label for="email">Email</label>
          <input id="email" type="email" placeholder="Enter email" required>

          <label for="password">Password</label>
          <input id="password" type="password" placeholder="Enter password"
            minlength="6" required>

          ${
            signup
              ? `<label for="confirm">Confirm Password</label>
                 <input id="confirm" type="password"
                   placeholder="Confirm password" required>`
              : ""
          }

          <button class="btn btn-primary" type="submit">
            ${signup ? "Create Account" : "Login"}
          </button>
        </form>

        <p class="muted auth-switch">
          ${signup ? "Already have an account?" : "New here?"}
          <a href="#${signup ? "login" : "signup"}">
            ${signup ? "Login" : "Create an account"}
          </a>
        </p>

      </div>
    </div>
  `;
}

async function submitAuth(event, signup) {
  event.preventDefault();

  const body = {
    email: document.getElementById("email").value.trim(),
    password: document.getElementById("password").value,
  };

  if (signup) {
    if (
      body.password !== document.getElementById("confirm").value
    ) {
      return toast("Passwords do not match");
    }

    body.username = document.getElementById("username").value.trim();
  }

  try {
    const data = await api("/auth/" + (signup ? "signup" : "login"), {
      method: "POST",
      body: JSON.stringify(body),
    });

    if (signup) {
      toast("Account created successfully");
      go("login");
      return;
    }

    me = data.user;
    renderNav();

    toast("Welcome back 🎬");

    if (me?.is_admin) {
      go("admin");
    } else {
      go("home");
    }
  } catch (error) {
    toast(error.message);
  }
}

async function logout() {
  try {
    await api("/auth/logout", { method: "POST" });
  } catch (error) {
    console.error("Logout request failed:", error);
  }

  me = null;
  renderNav();
  go("login");
}

// ======================================================
// ADMIN DASHBOARD
// ======================================================

async function admin() {
  if (!need()) return;

  if (!me?.is_admin) {
    toast("Admin access required");
    go("home");
    return;
  }

  app.innerHTML = `
    <div class="wrap admin-dashboard">

      <header class="admin-heading">
        <div class="admin-heading-icon">🛡️</div>
        <div>
          <div class="eyebrow">CONTROL CENTER</div>
          <h1>Admin <span>Dashboard</span></h1>
          <p>Overview of your platform statistics and user activity.</p>
        </div>
      </header>

      <div class="metric-grid">

        <article class="metric metric-users">
          <div class="metric-top">
            <span class="metric-icon">♟</span>
            <span class="metric-label">Users</span>
          </div>
          <b id="statUsers">—</b>
          <p>Total registered users</p>
        </article>

        <article class="metric metric-reviews">
          <div class="metric-top">
            <span class="metric-icon">★</span>
            <span class="metric-label">Reviews</span>
          </div>
          <b id="statReviews">—</b>
          <p>Total movie reviews</p>
        </article>

        <article class="metric metric-favorites">
          <div class="metric-top">
            <span class="metric-icon">♥</span>
            <span class="metric-label">Favorites</span>
          </div>
          <b id="statFavorites">—</b>
          <p>Total favorite movies</p>
        </article>

        <article class="metric metric-rating">
          <div class="metric-top">
            <span class="metric-icon">★</span>
            <span class="metric-label">Avg Rating</span>
          </div>
          <b id="statRating">—</b>
          <p>Platform average rating</p>
        </article>

      </div>

      <section class="admin-panel section">

        <div class="admin-panel-heading">
          <div>
            <h2>👥 Users</h2>
            <p>Manage registered users on your platform.</p>
          </div>
          <span class="panel-count" id="usersCount">Loading...</span>
        </div>

        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>#</th>
                <th>Username</th>
                <th>Email</th>
              </tr>
            </thead>
            <tbody id="adminUsers">
              <tr><td colspan="3">Loading users...</td></tr>
            </tbody>
          </table>
        </div>

      </section>

      <section class="admin-panel section">

        <div class="admin-panel-heading">
          <div>
            <h2>💬 Feedback</h2>
            <p>Recent movie feedback and reviews from users.</p>
          </div>
          <span class="panel-count" id="feedbackCount">Loading...</span>
        </div>

        <div class="admin-feedback-list" id="adminFeedback">
          <div class="loading">Loading feedback...</div>
        </div>

      </section>

    </div>
  `;

  try {
    const [stats, users, feedback] = await Promise.all([
      api("/admin/stats"),
      api("/admin/users"),
      api("/admin/feedback"),
    ]);

    document.getElementById("statUsers").textContent =
      stats.users ?? 0;

    document.getElementById("statReviews").textContent =
      stats.reviews ?? 0;

    document.getElementById("statFavorites").textContent =
      stats.favorites ?? 0;

    document.getElementById("statRating").textContent =
      stats.average_rating ?? "—";

    document.getElementById("usersCount").textContent =
      `${users.length} users`;

    document.getElementById("feedbackCount").textContent =
      `${feedback.length} reviews`;

    document.getElementById("adminUsers").innerHTML =
      users.length
        ? users.map((user, index) => `
            <tr>
              <td>${index + 1}</td>
              <td>
                <div class="admin-user-name">
                  <span class="admin-avatar">
                    ${esc((user.username || "?").charAt(0).toUpperCase())}
                  </span>
                  <strong>${esc(user.username || "Unknown")}</strong>
                </div>
              </td>
              <td>${esc(user.email || "")}</td>
            </tr>
          `).join("")
        : `<tr><td colspan="3">No users found.</td></tr>`;

    document.getElementById("adminFeedback").innerHTML =
      feedback.length
        ? feedback.map((review) => `
            <article class="admin-review">

              <div class="admin-review-icon">🎬</div>

              <div class="admin-review-content">
                <div class="admin-review-title">
                  <strong>${esc(review.movie_name || "Movie Review")}</strong>
                  <span class="stars">
                    ${"★".repeat(
                      Math.max(0, Math.min(5, Number(review.rating) || 0))
                    )}
                  </span>
                </div>
                <p>${esc(review.comment || "No comment provided.")}</p>
              </div>

              <button
                class="btn btn-danger admin-delete"
                onclick="deleteFeedback(${Number(review.id)})"
              >
                🗑 Delete
              </button>

            </article>
          `).join("")
        : `<div class="empty">No feedback available yet.</div>`;

  } catch (error) {
    app.innerHTML = `
      <div class="wrap empty">
        <h2>Unable to load Admin Dashboard</h2>
        <p>${esc(error.message)}</p>
        <button class="btn btn-primary" onclick="admin()">Try Again</button>
      </div>
    `;
  }
}

async function deleteFeedback(id) {
  if (!confirm("Are you sure you want to delete this feedback?")) {
    return;
  }

  try {
    await api("/admin/feedback/" + id, {
      method: "DELETE",
    });

    toast("Feedback deleted");
    admin();
  } catch (error) {
    toast(error.message);
  }
}
