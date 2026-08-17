# 🎬 Movie Recommendation System

A full-stack movie recommendation web application built with **FastAPI, HTML, CSS, JavaScript, and Machine Learning**.

The system allows users to search for movies, view movie details, get personalized recommendations using **TF-IDF**, explore movies through **TMDB**, and manage their account, favorites, and feedback.

## 🚀 Features

* 🔐 User Signup & Login
* 🚪 Secure Logout
* 🎬 Movie Search
* 🤖 TF-IDF based Movie Recommendations
* 🎥 TMDB movie information and posters
* ⭐ Movie Ratings
* ❤️ Add / Remove Favorites
* 💬 User Feedback
* 👤 User Profile
* 🛠️ Admin functionality
* 📱 Responsive web interface
* ⚡ FastAPI backend
* 🎨 HTML, CSS & JavaScript frontend

## 🛠️ Tech Stack

### Frontend

* HTML5
* CSS3
* JavaScript

### Backend

* Python
* FastAPI
* Uvicorn

### Machine Learning

* Scikit-learn
* TF-IDF Vectorization
* Cosine Similarity
* NumPy
* Pandas
* SciPy

### Database

* SQLite

### External API

* TMDB API

### Authentication & Security

* bcrypt
* Starlette Session Middleware
* Environment variables using `.env`

## 📂 Project Structure

```text
movie-recommendation-system/
│
├── frontend/
│   └── index.html
│
├── static/
│   ├── css/
│   └── js/
│
├── model/
│   ├── df.pkl
│   ├── indices.pkl
│   ├── tfidf.pkl
│   └── tfidf_matrix.pkl
│
├── main.py
├── database.py
├── requirements.txt
├── run.bat
├── .env.example
├── .gitignore
└── README.md
```

## 🧠 How Recommendation Works

The recommendation system uses **TF-IDF (Term Frequency-Inverse Document Frequency)** to convert movie information into numerical vectors.

It then uses **Cosine Similarity** to compare movies and find movies that are similar to the movie selected by the user.

The application combines the local recommendation model with **TMDB API** data to provide movie posters, ratings, release dates, and other movie information.

## 🔑 TMDB API Setup

This project requires a TMDB API key.

Create a `.env` file in the project root:

```env
TMDB_API_KEY=your_tmdb_api_key
SESSION_SECRET=your_secret_key
ADMIN_EMAIL=your_admin_email
```

**Important:** Never upload your `.env` file to GitHub.

The `.env` file is already excluded through `.gitignore`.

## ⚙️ Installation

Clone the repository:

```bash
git clone https://github.com/ganeshborase769/movie-recommendation-system.git
```

Go to the project directory:

```bash
cd movie-recommendation-system
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment on Windows:

```powershell
venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your `.env` file using `.env.example` and add your TMDB API key.

## ▶️ Run the Application

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

The application will run at:

```text
http://127.0.0.1:8000
```

Open the URL in your browser.

## 🔍 API

The backend provides APIs for:

* Authentication
* Movie search
* Movie recommendations
* TMDB movie data
* Favorites
* Feedback
* User information
* Health check

FastAPI automatically provides API documentation at:

```text
http://127.0.0.1:8000/docs
```

## 📊 Machine Learning Model

The project contains pre-trained recommendation resources:

* `df.pkl` — movie dataset
* `indices.pkl` — movie title index mapping
* `tfidf.pkl` — TF-IDF vectorizer
* `tfidf_matrix.pkl` — TF-IDF feature matrix

These files are used by the FastAPI backend to generate movie recommendations.

## 🔒 Security

Sensitive configuration is stored in environment variables.

The following files are excluded from Git:

```text
.env
venv/
__pycache__/
*.pyc
movie_rec.db
frontend.zip
```

## 📌 Future Improvements

* 🎞️ Trending Movies section
* 🌟 Top Rated Movies section
* 🇮🇳 Bollywood movie discovery
* 🎭 Genre-based search
* 👨‍🎤 Actor-based search
* 🎯 Improved recommendation algorithms
* ☁️ Cloud deployment
* 📱 Further UI/UX improvements

## 👨‍💻 Developer

**Ganesh Borase**

MCA Student | Aspiring Full Stack Developer

GitHub:
https://github.com/ganeshborase769

## 📄 License

This project is created for educational and portfolio purposes.
