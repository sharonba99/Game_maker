from flask import Blueprint, request, jsonify
from utils.db import db
from models import TriviaQuestion, User


play_bp = Blueprint("play_bp", __name__)

@play_bp.get("/leaderboards")
def show_leaderboards():
    rows = User.query.with_entities(User.id, User.username, User.points).all()
    data = [{r.username:r.points} for r in rows]
    return jsonify({"leaderboards":data}), 200

@play_bp.put("/add/<int:user_id>")
def add_points(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify(
            {"ok": False, "error": {"code": "not_found", "message": f"User with ID {user_id} not found"}}), 404
    user.points += 10
    db.session.commit()
    return f"User {user.username} got 10 points", 200