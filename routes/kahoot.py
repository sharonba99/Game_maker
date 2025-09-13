
from flask import Blueprint, request, jsonify
from sqlalchemy import func
from utils.db import db, User, Topic, Question, Game, Player, Answer
import json, random

kahoot_bp = Blueprint("kahoot_bp", __name__)

@kahoot_bp.get("/topics")
def list_topics():
    topics = Topic.query.all()
    return jsonify([{"id": t.id, "name": t.name} for t in topics]), 200

@kahoot_bp.post("/games/create")
def create_game():
    data = request.get_json(silent=True) or {}
    topic_id = data.get("topic_id")
    difficulty = (data.get("difficulty") or "Any").capitalize()  # Any/Easy/Medium/Hard
    num_questions = int(data.get("num_questions") or 10)

    if not topic_id:
        return jsonify({"error":"topic_id is required"}), 400

    q_query = Question.query.filter_by(topic_id=topic_id)
    if difficulty != "Any":
        q_query = q_query.filter_by(difficulty=difficulty)

    qs = q_query.all()
    if not qs:
        return jsonify({"error":"No questions match this topic/difficulty"}), 404

    order = [q.id for q in qs]
    random.shuffle(order)
    order = order[:num_questions]

    game = Game(topic_id=topic_id, order_json=json.dumps(order), current_index=0, is_active=True, difficulty=difficulty)
    db.session.add(game)
    db.session.commit()
    return jsonify({"message":"game created","game_id":game.id,"question_count":len(order), "difficulty":difficulty}), 201

@kahoot_bp.post("/games/<int:game_id>/join")
def join_game(game_id):
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    if not username:
        return jsonify({"error":"username is required"}), 400
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error":"user not found"}), 404
    game = Game.query.get(game_id)
    if not game or not game.is_active:
        return jsonify({"error":"game not found or inactive"}), 404
    existing = Player.query.filter_by(user_id=user.id, game_id=game_id).first()
    if existing:
        return jsonify({"message":"already joined","player_id":existing.id}), 200
    player = Player(user_id=user.id, game_id=game_id, score=0)
    db.session.add(player)
    db.session.commit()
    return jsonify({"message":"joined","player_id":player.id}), 201

@kahoot_bp.get("/games/<int:game_id>/state")
def game_state(game_id):
    game = Game.query.get(game_id)
    if not game:
        return jsonify({"error":"game not found"}), 404
    order = json.loads(game.order_json)
    return jsonify({
        "game_id": game.id,
        "topic": game.topic.name,
        "difficulty": game.difficulty,
        "current_index": game.current_index,
        "total_questions": len(order),
        "is_active": game.is_active
    }), 200

@kahoot_bp.get("/games/<int:game_id>/question")
def get_question(game_id):
    idx = request.args.get("index", type=int)
    game = Game.query.get(game_id)
    if not game:
        return jsonify({"error":"game not found"}), 404
    order = json.loads(game.order_json)
    if idx is None:
        idx = game.current_index
    if idx < 0 or idx >= len(order):
        return jsonify({"error":"index out of range"}), 400
    q = Question.query.get(order[idx])
    payload = {
        "index": idx,
        "question_id": q.id,
        "text": q.text,
        "choices": {"A": q.choice_a, "B": q.choice_b, "C": q.choice_c, "D": q.choice_d},
        "difficulty": q.difficulty
    }
    return jsonify(payload), 200

@kahoot_bp.post("/games/<int:game_id>/answer")
def submit_answer(game_id):
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    question_id = data.get("question_id")
    selected = data.get("selected")
    if not username or not question_id or selected not in ["A","B","C","D"]:
        return jsonify({"error":"username, question_id and selected(A/B/C/D) are required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error":"user not found"}), 404
    player = Player.query.filter_by(user_id=user.id, game_id=game_id).first()
    if not player:
        return jsonify({"error":"player not joined"}), 400
    q = Question.query.get(question_id)
    if not q:
        return jsonify({"error":"question not found"}), 404

    if Answer.query.filter_by(player_id=player.id, question_id=question_id).first():
        return jsonify({"error":"already answered"}), 409

    correct = (selected == q.correct)
    base_points = {"Easy":100, "Medium":200, "Hard":300}.get(q.difficulty, 100)
    points = base_points if correct else 0
    ans = Answer(player_id=player.id, question_id=question_id, selected=selected, is_correct=correct)
    player.score += points
    db.session.add(ans)
    db.session.commit()
    return jsonify({"correct":correct, "points_awarded":points, "total_score":player.score, "difficulty": q.difficulty}), 201

@kahoot_bp.post("/games/<int:game_id>/next")
def next_question(game_id):
    game = Game.query.get(game_id)
    if not game:
        return jsonify({"error":"game not found"}), 404
    order = json.loads(game.order_json)
    if game.current_index + 1 < len(order):
        game.current_index += 1
        db.session.commit()
        return jsonify({"message":"advanced","current_index":game.current_index}), 200
    else:
        game.is_active = False
        db.session.commit()
        return jsonify({"message":"game finished","current_index":game.current_index}), 200

@kahoot_bp.get("/games/<int:game_id>/leaderboard")
def leaderboard(game_id):
    rows = (db.session.query(Player)
            .filter(Player.game_id==game_id)
            .order_by(Player.score.desc(), Player.joined_at.asc())
            .all())
    lb = [{"username": r.user.username, "score": r.score} for r in rows]
    return jsonify(lb), 200
