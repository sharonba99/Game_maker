# app.py
import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from utils.db import db
from blueprints.users import user_bp
from blueprints.library import library_bp


def create_app() -> Flask:
    """
    Flask application factory.
    - טוען .env (אם קיים)
    - מוודא תיקיית instance (שם קובץ ה-SQLite)
    - מגדיר CORS לפרונטאנד
    - רושם Blueprints
    """
    load_dotenv()

    app = Flask("Trivia-creator", instance_relative_config=True)

    # make sure instance/ exists (DB will live here)
    os.makedirs(app.instance_path, exist_ok=True)

    # ---------- Config ----------
    default_sqlite = "sqlite:///" + os.path.join(app.instance_path, "users.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", default_sqlite)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # CORS – (5173 = Vite, 3000 = CRA)
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
    origins_list = [o.strip() for o in cors_origins.split(",") if o.strip()]
    CORS(app, origins=origins_list, supports_credentials=True)

    # ---------- Init ----------
    db.init_app(app)

    # ---------- Health ----------
    @app.get("/")
    def root():
        return "Welcome to Trivia maker"

    # ---------- Blueprints ----------
    app.register_blueprint(user_bp, url_prefix="/users")
    app.register_blueprint(library_bp, url_prefix="/library")

    return app


if __name__ == "__main__":
    app = create_app()

    # create tables if they don't exist
    with app.app_context():
        # beacuse of circular import
        from models import (
            User,
            TriviaQuestion,
            Quiz,
            QuizSession,
            QuizAnswerLog,
            LeaderboardEntry,
        )
        db.drop_all()
        db.create_all()

    port = int(os.getenv("PORT", "5001"))
    print(f">>> Flask on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
    
    with app.app_context():
        from sqlalchemy import inspect, text
        # ייצור טבלאות אם חסרות
        db.create_all()

        # הוספת העמודה duration_ms אם לא קיימת
        insp = inspect(db.engine)
        cols = [c['name'] for c in insp.get_columns('leaderboard_entry')]
        if 'duration_ms' not in cols:
            db.session.execute(text('ALTER TABLE leaderboard_entry ADD COLUMN duration_ms INTEGER'))
            db.session.commit()

