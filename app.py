from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
import sqlite3
import pickle
import requests
from tmdb_config import TMDB_API_KEY

app = Flask(__name__)
app.secret_key = 'secret123'

# Load model and data
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

movies_df = pd.read_csv("data/movies.csv")
ratings_df = pd.read_csv("data/ratings.csv")

# Setup database
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS history (user_id INTEGER, movie_id INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# TMDB fetch
def fetch_poster(movie_title):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_title}"
    response = requests.get(url)
    data = response.json()
    if data.get("results"):
        poster_path = data["results"][0].get("poster_path")
        return f"https://image.tmdb.org/t/p/w200{poster_path}" if poster_path else None
    return None

@app.route("/", methods=["GET"])
def home():
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already taken. Try another.", "danger")
        finally:
            conn.close()
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session["user_id"] = user[0]
            session["username"] = username
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/index", methods=["GET", "POST"])
def index():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))
    return redirect(url_for("recommend", user_id=user_id))

@app.route("/recommend/<int:user_id>")
def recommend(user_id):
    movie_ids = movies_df["movieId"].tolist()
    predictions = [model.predict(user_id, iid) for iid in movie_ids]
    predictions.sort(key=lambda x: x.est, reverse=True)
    top_n = predictions[:5]
    recommended = []
    for pred in top_n:
        title = movies_df[movies_df["movieId"] == pred.iid]["title"].values[0]
        poster = fetch_poster(title)
        recommended.append((title, poster))
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO history (user_id, movie_id) VALUES (?, ?)", (user_id, pred.iid))
        conn.commit()
        conn.close()

    return render_template("recommendations.html", recommendations=recommended)

if __name__ == "__main__":
    app.run(debug=True)