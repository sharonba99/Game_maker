import os
from trivia import trivia_bp
from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from utils.db import db
from users import user_bp

app = Flask("Trivia-creator")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
db.init_app(app)



@app.get("/")
def homepage():
    return "Welcome to Trivia maker"

app.register_blueprint(user_bp, url_prefix='/users')
app.register_blueprint(trivia_bp, url_prefix='/trivia')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5001)