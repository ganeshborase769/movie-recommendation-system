# 🎬 Movie Recommendation System

A web-based Movie Recommendation System that helps users discover movies and explore movie details using TMDB API and a recommendation engine.

## 🚀 Live Demo

- **Live Website:** [Add Your Vercel Deployment URL](https://vercel.com/)
- **GitHub Repository:** [Movie Recommendation System](https://github.com/ganeshborase769/movie-recommendation-system)

## ✨ Features

- 🎥 Movie recommendations
- 🔍 Movie discovery and search
- 🌐 Movie data integration using TMDB API
- 🔐 User authentication and account management
- 💾 Database integration using Turso
- 📱 Web-based user interface
- ☁️ Deployment using Vercel

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend development |
| FastAPI | Backend API framework |
| SQLite / Turso | Database storage |
| TMDB API | Movie data |
| Pandas & NumPy | Data processing |
| Scikit-learn | Machine learning utilities |
| HTML, CSS, JavaScript | Web interface |
| Vercel | Deployment |

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/ganeshborase769/movie-recommendation-system.git
```

### 2. Navigate to the Project Directory

```bash
cd movie-recommendation-system
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the project root and add the required configuration:

```env
TMDB_API_KEY=your_tmdb_api_key
TURSO_DATABASE_URL=your_turso_database_url
TURSO_AUTH_TOKEN=your_turso_auth_token
SESSION_SECRET=your_secure_random_secret
```

Replace the placeholder values with your own credentials.

**Security:** Never commit your `.env` file, API keys, or database tokens to GitHub.

### 6. Run the Application

```bash
uvicorn main:app --reload
```

Open the local application at:

`http://127.0.0.1:8000`

If the project uses a different frontend or startup configuration, follow the corresponding project settings.

## ☁️ Deployment

The application is deployed using Vercel.

To configure deployment:

1. Import the GitHub repository into Vercel.
2. Configure the required environment variables in Project Settings.
3. Select the appropriate build and deployment configuration.
4. Deploy the application.
5. Test authentication, movie data retrieval, and recommendations.

## 🔑 API Configuration

This project uses the TMDB API to retrieve movie-related information.

Get an API key from [The Movie Database (TMDB)](https://www.themoviedb.org/).

## 📂 Project Structure

```text
movie-recommendation-system/
├── main.py
├── database.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

*Note: Update this structure to match the actual files and folders in your repository.*

## 🔮 Future Enhancements

- Improve recommendation accuracy
- Add more movie filtering options
- Enhance the user interface
- Add personalized recommendations
- Improve performance and error handling

## 👨‍💻 Author

**Ganesh Borase**

GitHub: [@ganeshborase769](https://github.com/ganeshborase769)

## 📄 Disclaimer

This project uses the TMDB API for movie-related data. Movie data and images are provided by TMDB and are subject to its terms and attribution requirements.
