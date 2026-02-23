from __future__ import annotations

import sqlite3
from pathlib import Path
from uuid import uuid4

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "maintenance.db"
UPLOAD_DIR = BASE_DIR / "static" / "uploads"

app = Flask(__name__)
app.config["SECRET_KEY"] = "skipta-ut-i-sannri-leynd-i-framleidslu"
app.config["UPLOAD_FOLDER"] = str(UPLOAD_DIR)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


# TODO: replace with real values via environment variables in production
DEFAULT_USERNAME = "eigandi"
DEFAULT_PASSWORD = "hus1234"


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error: Exception | None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = sqlite3.connect(DATABASE_PATH)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS repairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            cost REAL NOT NULL,
            repair_date TEXT NOT NULL,
            image_path TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    user = db.execute("SELECT id FROM users WHERE username = ?", (DEFAULT_USERNAME,)).fetchone()
    if user is None:
        db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (DEFAULT_USERNAME, generate_password_hash(DEFAULT_PASSWORD)),
        )

    db.commit()
    db.close()


@app.before_request
def protect_routes() -> None:
    if request.endpoint in {"login", "static"}:
        return
    if not session.get("user_id"):
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if not user or not check_password_hash(user["password_hash"], password):
            flash("Rangt notendanafn eða lykilorð", "error")
            return render_template("login.html")

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/", methods=["GET", "POST"])
def index():
    db = get_db()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        repair_date = request.form.get("repair_date", "")

        try:
            cost = float(request.form.get("cost", "0"))
        except ValueError:
            flash("Kostnaður þarf að vera tala", "error")
            return redirect(url_for("index"))

        if not title or not description or not repair_date:
            flash("Vinsamlegast fylltu út alla skyldureiti", "error")
            return redirect(url_for("index"))

        image = request.files.get("image")
        image_path = None
        if image and image.filename:
            extension = Path(image.filename).suffix.lower()
            safe_name = f"{uuid4().hex}{extension}"
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            destination = UPLOAD_DIR / safe_name
            image.save(destination)
            image_path = f"uploads/{safe_name}"

        db.execute(
            """
            INSERT INTO repairs (title, description, cost, repair_date, image_path)
            VALUES (?, ?, ?, ?, ?)
            """,
            (title, description, cost, repair_date, image_path),
        )
        db.commit()
        flash("Viðgerð vistuð", "success")
        return redirect(url_for("index"))

    repairs = db.execute(
        "SELECT * FROM repairs ORDER BY repair_date DESC, id DESC"
    ).fetchall()
    total_cost = db.execute("SELECT COALESCE(SUM(cost), 0) AS total FROM repairs").fetchone()["total"]

    return render_template("index.html", repairs=repairs, total_cost=total_cost)


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
