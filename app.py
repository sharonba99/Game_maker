import os

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from utils.db import db
from blueprints.users import user_bp
from blueprints.library import library_bp
from flask import request, redirect


def strip_newlines_in_path():
    if (
        "%0A" in request.full_path
        or "\n" in request.full_path
        or "\r" in request.full_path
    ):
        clean = request.path.replace("\n", "").replace("\r", "")
        return redirect(clean or "/", code=307)


def create_app() -> Flask:
    """Create and configure the Flask application."""
    load_dotenv()  # load .env if exists

    app = Flask("Trivia-creator", instance_relative_config=True)

    # make sure /instance exists (DB will live here)
    os.makedirs(app.instance_path, exist_ok=True)

    # --- Config ---
    default_sqlite = "sqlite:///" + os.path.join(app.instance_path, "users.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", default_sqlite)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # secrets (override in .env for production)
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-jwt-change-me")

    # CORS for frontend (React dev servers)
    cors_origins = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
    )
    CORS(
        app,
        origins=[o.strip() for o in cors_origins.split(",") if o.strip()],
        supports_credentials=True,
    )

    # init DB
    db.init_app(app)

    # --- Routes ---
    @app.get("/")
    def root():
        return "Welcome to Trivia maker"

    # Blueprints
    app.register_blueprint(user_bp, url_prefix="/users")
    app.register_blueprint(library_bp, url_prefix="/library")

    return app


if __name__ == "__main__":
    app = create_app()

    # create tables on first run
    with app.app_context():
        from models import (
            User,
            TriviaQuestion,
            QuizSession,
            LeaderboardEntry,
        )  # noqa: F401

        db.create_all()

    port = int(os.getenv("PORT", "5001"))
    print(f">>> Flask is starting on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
