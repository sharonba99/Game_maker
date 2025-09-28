from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import db
from models import User

user_bp = Blueprint("user_bp", __name__)

@user_bp.get("/")
def list_users():
    rows = User.query.with_entities(User.id, User.username).all()
    data = [{"id": r.id, "username": r.username} for r in rows]
    return jsonify({"ok": True, "data": data}), 200

@user_bp.post("/signup")
def signup():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"ok": False, "error": {"code": "bad_request", "message": "username and password are required"}}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"ok": False, "error": {"code": "duplicate", "message": "user already exists"}}), 409

    u = User(username=username, password_hash=generate_password_hash(password))
    db.session.add(u)
    db.session.commit()
    return jsonify({"ok": True, "data": {"id": u.id, "username": u.username}}), 201

@user_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"ok": False, "error": {"code": "bad_request", "message": "username and password are required"}}), 400

    u = User.query.filter_by(username=username).first()
    if not u or not check_password_hash(u.password_hash, password):
        return jsonify({"ok": False, "error": {"code": "unauthorized", "message": "username or password incorrect"}}), 401

    return jsonify({"ok": True, "data": {"message": "login successful"}}), 200

@user_bp.get("/<int:user_id>")
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify(
            {"ok": False, "error": {"code": "not_found", "message": f"User with ID {user_id} not found"}}), 404

    return jsonify({
        "ok": True,
        "data": {
            "id": user.id,
            "username": user.username
        }
    }), 200

@user_bp.delete("/<int:user_id>")
def del_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify(
            {"ok": False, "error": {"code": "not_found", "message": f"User with ID {user_id} not found"}}), 404
    db.session.delete(user)
    db.session.commit()
    return f"User {user.username} has been deleted", 200