import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from flask_migrate import Migrate

from utils.db import db  # SQLAlchemy()

def create_app() -> Flask:
    """Trivia-creator backend (clean daily-run version)."""
    load_dotenv()

    app = Flask("Trivia-creator", instance_relative_config=True)

    # make sure instance/ exists (SQLite will live here by default)
    os.makedirs(app.instance_path, exist_ok=True)
    default_sqlite = "sqlite:///" + os.path.join(app.instance_path, "users.db")

    # ---------- Config ----------
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", default_sqlite)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # CORS (5173=Vite, 3000=CRA) – can be overridden via CORS_ORIGINS in .env
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
    origins_list = [o.strip() for o in cors_origins.split(",") if o.strip()]
    CORS(app, origins=origins_list, supports_credentials=True)

    # ---------- Init ----------
    db.init_app(app)
    Migrate(app, db)

   # import & register blueprints
    from routes.library import library_bp
    from routes.users import user_bp

    app.register_blueprint(library_bp, url_prefix="/library")
    app.register_blueprint(user_bp, url_prefix="/users")

    # (important) import models so Alembic/Autogenerate "sees" them
    with app.app_context():
        from models import (
            User, TriviaQuestion, Quiz, QuizSession, QuizAnswerLog, LeaderboardEntry,
        )

        # auto-seed
        from utils.seeder import auto_seed
        auto_seed()


    # ---------- Health ----------
    @app.get("/")
    def root():
        return jsonify({"ok": True, "db": str(db.engine.url)})

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", "5001"))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    print(f">>> Flask on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
