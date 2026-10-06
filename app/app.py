import os
import secrets
import sqlite3
import string

from flask import Flask, g, jsonify, redirect, request

ALPHABET = string.ascii_letters + string.digits


def create_app(db_path=None):
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path or os.getenv("DB_PATH", "urls.db")

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DB_PATH"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    with app.app_context():
        get_db().execute(
            "CREATE TABLE IF NOT EXISTS urls ("
            "code TEXT PRIMARY KEY, url TEXT NOT NULL, hits INTEGER DEFAULT 0)"
        )
        get_db().commit()

    @app.get("/healthz")
    def healthz():
        get_db().execute("SELECT 1")
        return jsonify(status="ok", version="v2")

    @app.post("/api/shorten")
    def shorten():
        data = request.get_json(silent=True) or {}
        url = data.get("url", "")
        if not url.startswith(("http://", "https://")):
            return jsonify(error="url must start with http:// or https://"), 400
        code = "".join(secrets.choice(ALPHABET) for _ in range(7))
        db = get_db()
        db.execute("INSERT INTO urls (code, url) VALUES (?, ?)", (code, url))
        db.commit()
        return jsonify(code=code, short_url=f"{request.host_url}{code}"), 201

    @app.get("/api/stats/<code>")
    def stats(code):
        row = get_db().execute(
            "SELECT url, hits FROM urls WHERE code = ?", (code,)
        ).fetchone()
        if row is None:
            return jsonify(error="not found"), 404
        return jsonify(code=code, url=row["url"], hits=row["hits"])

    @app.get("/<code>")
    def go(code):
        db = get_db()
        row = db.execute("SELECT url FROM urls WHERE code = ?", (code,)).fetchone()
        if row is None:
            return jsonify(error="not found"), 404
        db.execute("UPDATE urls SET hits = hits + 1 WHERE code = ?", (code,))
        db.commit()
        return redirect(row["url"], code=302)

    return app


app = create_app()
