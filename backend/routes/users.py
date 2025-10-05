from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from utils.db import db
from utils.helpers import j_ok, j_err, norm
from models import User

user_bp = Blueprint("user_bp", __name__)

@user_bp.post("/signup")
def signup():
    data = request.get_json(silent=True) or {}
    username = norm(data.get("username"))
    password = data.get("password")

    if not username or not password:
        return j_err("bad_request", "username & password required", 400)

    if User.query.filter_by(username=username).first():
        return j_err("duplicate", "username already exists", 409)

    hashed = generate_password_hash(password)
    user = User(username=username, password_hash=hashed)
    db.session.add(user)
    db.session.commit()
    return j_ok({"id": user.id, "username": user.username}, 201)


@user_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = norm(data.get("username"))
    password = data.get("password") or ""

    if not username or not password:
        return j_err("bad_request", "username & password required", 400)

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return j_err("unauthorized", "invalid username or password", 401)

    return j_ok({"user_id": user.id, "username": user.username})


