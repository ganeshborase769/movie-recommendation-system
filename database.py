import sqlite3
from pathlib import Path

DATABASE = str(Path(__file__).resolve().parent / 'movie_rec.db')

def get_connection():
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn=get_connection(); cur=conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS feedback(id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, movie_id INTEGER, movie_name TEXT, rating INTEGER, comment TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS favorites(id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT NOT NULL, movie_id INTEGER NOT NULL, movie_name TEXT NOT NULL, poster TEXT)''')
    try: cur.execute('ALTER TABLE feedback ADD COLUMN movie_id INTEGER')
    except sqlite3.OperationalError: pass
    try: cur.execute('ALTER TABLE feedback ADD COLUMN created_at TEXT DEFAULT CURRENT_TIMESTAMP')
    except sqlite3.OperationalError: pass
    conn.commit(); conn.close()

def add_user(username,email,password):
    conn=get_connection(); cur=conn.cursor()
    try:
        cur.execute('INSERT INTO users(username,email,password) VALUES(?,?,?)',(username,email.lower().strip(),password)); conn.commit(); return True
    except sqlite3.IntegrityError: return False
    finally: conn.close()

def get_user(email):
    conn=get_connection(); cur=conn.cursor(); cur.execute('SELECT * FROM users WHERE email=?',(email.lower().strip(),)); row=cur.fetchone(); conn.close(); return row

def get_all_users():
    conn=get_connection(); cur=conn.cursor(); cur.execute('SELECT id,username,email FROM users ORDER BY id DESC'); rows=cur.fetchall(); conn.close(); return rows

def get_total_users():
    conn=get_connection(); cur=conn.cursor(); cur.execute('SELECT COUNT(*) FROM users'); n=cur.fetchone()[0]; conn.close(); return n

def add_feedback(user_email,movie_name,rating,comment,movie_id=None):
    conn=get_connection(); cur=conn.cursor(); cur.execute('INSERT INTO feedback(user_email,movie_id,movie_name,rating,comment) VALUES(?,?,?,?,?)',(user_email,movie_id,movie_name,rating,comment)); conn.commit(); conn.close()

def get_feedback():
    conn=get_connection(); cur=conn.cursor(); cur.execute('SELECT * FROM feedback ORDER BY id DESC'); rows=cur.fetchall(); conn.close(); return rows

def get_feedback_for_movie(movie_name,limit=5):
    conn=get_connection(); cur=conn.cursor(); cur.execute('SELECT * FROM feedback WHERE movie_name=? ORDER BY id DESC LIMIT ?',(movie_name,limit)); rows=cur.fetchall(); conn.close(); return rows

def get_movie_rating_stats(movie_name):
    conn=get_connection(); cur=conn.cursor(); cur.execute('SELECT AVG(rating) avg_rating, COUNT(*) total FROM feedback WHERE movie_name=?',(movie_name,)); row=cur.fetchone(); conn.close(); return (round(row['avg_rating'],1),row['total']) if row and row['avg_rating'] is not None else (None,0)

def get_total_feedback():
    conn=get_connection(); cur=conn.cursor(); cur.execute('SELECT COUNT(*) FROM feedback'); n=cur.fetchone()[0]; conn.close(); return n

def get_average_platform_rating():
    conn=get_connection(); cur=conn.cursor(); cur.execute('SELECT AVG(rating) FROM feedback'); n=cur.fetchone()[0]; conn.close(); return round(n,2) if n is not None else None

def get_top_rated_movies(limit=5):
    conn=get_connection(); cur=conn.cursor(); cur.execute('SELECT movie_name,AVG(rating) avg_rating,COUNT(*) total FROM feedback GROUP BY movie_name ORDER BY avg_rating DESC,total DESC LIMIT ?',(limit,)); rows=cur.fetchall(); conn.close(); return rows

def delete_feedback(feedback_id):
    conn=get_connection(); cur=conn.cursor(); cur.execute('DELETE FROM feedback WHERE id=?',(feedback_id,)); conn.commit(); conn.close()

def add_favorite(user_email,movie_id,movie_name,poster):
    conn=get_connection(); cur=conn.cursor(); cur.execute('SELECT 1 FROM favorites WHERE user_email=? AND movie_id=?',(user_email,movie_id))
    if cur.fetchone(): conn.close(); return False
    cur.execute('INSERT INTO favorites(user_email,movie_id,movie_name,poster) VALUES(?,?,?,?)',(user_email,movie_id,movie_name,poster)); conn.commit(); conn.close(); return True

def get_favorites(user_email):
    conn=get_connection(); cur=conn.cursor(); cur.execute('SELECT movie_id,movie_name,poster FROM favorites WHERE user_email=? ORDER BY id DESC',(user_email,)); rows=cur.fetchall(); conn.close(); return rows

def is_favorite(user_email,movie_id):
    conn=get_connection(); cur=conn.cursor(); cur.execute('SELECT 1 FROM favorites WHERE user_email=? AND movie_id=?',(user_email,movie_id)); found=cur.fetchone() is not None; conn.close(); return found

def remove_favorite(user_email,movie_id):
    conn=get_connection(); cur=conn.cursor(); cur.execute('DELETE FROM favorites WHERE user_email=? AND movie_id=?',(user_email,movie_id)); conn.commit(); conn.close()

def get_total_favorites():
    conn=get_connection(); cur=conn.cursor(); cur.execute('SELECT COUNT(*) FROM favorites'); n=cur.fetchone()[0]; conn.close(); return n

def get_most_favorited_movies(limit=5):
    conn=get_connection(); cur=conn.cursor(); cur.execute('SELECT movie_name,poster,COUNT(*) saves FROM favorites GROUP BY movie_id,movie_name ORDER BY saves DESC LIMIT ?',(limit,)); rows=cur.fetchall(); conn.close(); return rows
