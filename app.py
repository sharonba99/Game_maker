
from flask import Flask, send_from_directory
from utils.db import db, seed_data
from routes.kahoot import kahoot_bp

def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="/")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JSON_AS_ASCII"] = False

    db.init_app(app)
    with app.app_context():
        db.create_all()
        seed_data()  # seed users, topics, questions (with difficulty)

    @app.get("/health")
    def health():
        return {"status":"ok"}

    app.register_blueprint(kahoot_bp, url_prefix="/api/kahoot")

    @app.get("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
