from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import db
from models import User

user_bp = Blueprint("user_bp", __name__)

# ---------- helpers ----------
def j_ok(data=None, status=200):
    return jsonify({"ok": True, "data": data}), status

def j_err(code, msg, status=400):
    return jsonify({"ok": False, "error": {"code": code, "message": msg}}), status

# ---------- routes ----------
@user_bp.get("/")
def list_users():
    rows = User.query.with_entities(User.id, User.username).all()
    return j_ok([{"id": r.id, "username": r.username} for r in rows])

@user_bp.post("/signup")
def signup():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not password:
        return j_err("invalid", "Username and password required", 400)

    if User.query.filter_by(username=username).first():
        return j_err("exists", "Username already taken", 409)

    user = User(username=username, password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()
    return j_ok({"id": user.id, "username": user.username}, 201)

@user_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not password:
        return j_err("bad_request", "username and password are required", 400)

    u = User.query.filter_by(username=username).first()
    if not u or not check_password_hash(u.password_hash, password):
        return j_err("unauthorized", "username or password incorrect", 401)

    # No JWT: return user details to store locally on the client
    return j_ok({"user_id": u.id, "username": u.username}, 200)
