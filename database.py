
import os
from collections.abc import Mapping

import turso_serverless


def get_connection():
    database_url = os.getenv("TURSO_DATABASE_URL")
    auth_token = os.getenv("TURSO_AUTH_TOKEN")

    if not database_url or not auth_token:
        raise RuntimeError(
            "TURSO_DATABASE_URL or TURSO_AUTH_TOKEN is missing."
        )

    return turso_serverless.connect(
        database_url,
        auth_token=auth_token,
    )


class DbRow(Mapping):
    """Supports row['email'], row[0], and dict(row)."""

    def __init__(self, keys, values):
        self._keys = list(keys)
        self._values = tuple(values)
        self._data = dict(zip(self._keys, self._values))

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return self._data[key]

    def __iter__(self):
        return iter(self._keys)

    def __len__(self):
        return len(self._keys)


def fetch_one(cur):
    row = cur.fetchone()
    if row is None:
        return None

    columns = [column[0] for column in cur.description]
    return DbRow(columns, row)


def fetch_all(cur):
    columns = [column[0] for column in cur.description]
    return [DbRow(columns, row) for row in cur.fetchall()]


def create_tables():
    conn = get_connection()
    try:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT,
                movie_id INTEGER,
                movie_name TEXT,
                rating INTEGER,
                comment TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                movie_id INTEGER NOT NULL,
                movie_name TEXT NOT NULL,
                poster TEXT
            )
        """)

        conn.commit()
    finally:
        conn.close()


def add_user(username, email, password):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO users (username, email, password)
               VALUES (?, ?, ?)""",
            (username, email.lower().strip(), password),
        )
        conn.commit()
        return True
    except Exception as exc:
        if "unique" in str(exc).lower():
            return False
        raise
    finally:
        conn.close()


def get_user(email):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE email = ?",
            (email.lower().strip(),),
        )
        return fetch_one(cur)
    finally:
        conn.close()


def get_all_users():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, email FROM users ORDER BY id DESC"
        )
        return fetch_all(cur)
    finally:
        conn.close()


def get_total_users():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        return fetch_one(cur)[0]
    finally:
        conn.close()


def add_feedback(user_email, movie_name, rating, comment, movie_id=None):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO feedback
               (user_email, movie_id, movie_name, rating, comment)
               VALUES (?, ?, ?, ?, ?)""",
            (user_email, movie_id, movie_name, rating, comment),
        )
        conn.commit()
    finally:
        conn.close()


def get_feedback():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM feedback ORDER BY id DESC")
        return fetch_all(cur)
    finally:
        conn.close()


def get_feedback_for_movie(movie_name, limit=5):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT * FROM feedback
               WHERE movie_name = ? ORDER BY id DESC LIMIT ?""",
            (movie_name, limit),
        )
        return fetch_all(cur)
    finally:
        conn.close()


def get_movie_rating_stats(movie_name):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT AVG(rating) AS avg_rating, COUNT(*) AS total
               FROM feedback WHERE movie_name = ?""",
            (movie_name,),
        )
        row = fetch_one(cur)
        if row and row["avg_rating"] is not None:
            return round(row["avg_rating"], 1), row["total"]
        return None, 0
    finally:
        conn.close()


def get_total_feedback():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM feedback")
        return fetch_one(cur)[0]
    finally:
        conn.close()


def get_average_platform_rating():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT AVG(rating) FROM feedback")
        value = fetch_one(cur)[0]
        return round(value, 2) if value is not None else None
    finally:
        conn.close()


def get_top_rated_movies(limit=5):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT movie_name, AVG(rating) AS avg_rating,
                      COUNT(*) AS total
               FROM feedback GROUP BY movie_name
               ORDER BY avg_rating DESC, total DESC LIMIT ?""",
            (limit,),
        )
        return fetch_all(cur)
    finally:
        conn.close()


def delete_feedback(feedback_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM feedback WHERE id = ?", (feedback_id,)
        )
        conn.commit()
    finally:
        conn.close()


def add_favorite(user_email, movie_id, movie_name, poster):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM favorites WHERE user_email = ? AND movie_id = ?",
            (user_email, movie_id),
        )
        if cur.fetchone():
            return False

        cur.execute(
            """INSERT INTO favorites
               (user_email, movie_id, movie_name, poster)
               VALUES (?, ?, ?, ?)""",
            (user_email, movie_id, movie_name, poster),
        )
        conn.commit()
        return True
    finally:
        conn.close()


def get_favorites(user_email):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT movie_id, movie_name, poster FROM favorites
               WHERE user_email = ? ORDER BY id DESC""",
            (user_email,),
        )
        return fetch_all(cur)
    finally:
        conn.close()


def is_favorite(user_email, movie_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM favorites WHERE user_email = ? AND movie_id = ?",
            (user_email, movie_id),
        )
        return cur.fetchone() is not None
    finally:
        conn.close()


def remove_favorite(user_email, movie_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM favorites WHERE user_email = ? AND movie_id = ?",
            (user_email, movie_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_total_favorites():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM favorites")
        return fetch_one(cur)[0]
    finally:
        conn.close()


def get_most_favorited_movies(limit=5):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT movie_name, poster, COUNT(*) AS saves
               FROM favorites GROUP BY movie_id, movie_name
               ORDER BY saves DESC LIMIT ?""",
            (limit,),
        )
        return fetch_all(cur)
    finally:
        conn.close()
