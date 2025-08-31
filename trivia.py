from flask import Blueprint, request, jsonify
from utils.utils import trivia, users

current_id = 1
trivia_bp = Blueprint('trivia_bp', __name__)

@trivia_bp.get('/')
def show_trivia():
    return trivia

#adding questions
@trivia_bp.post('/add')
def add_trivia():
    global  current_id
    try:
        data = request.json
        data["id"] = current_id
        for question in trivia:
            if question['question'] == data['question']:
                return 'question already exists', 403
        trivia.append(data)
        current_id += 1
        return "question added", 201
    except Exception as e:
        return str(e), 200

#getting questions by id
@trivia_bp.get('/question/<int:id>')
def get_question(id):
    for question in trivia:
        if question.get('id') == id:
            return question
    return jsonify({'status': 'not found'}), 404

#adding points to users
@trivia_bp.put('/correct/<int:id>')
def add_points(id):
    for user in users:
        if user["id"] == id:
            user["points"] += 1
            return f"point added to {user["username"]}"
    return "No user found", 404

@trivia_bp.get('/leaderboards')
def show_leaderboard():
    sorted_data = sorted(users, key=lambda x: x["points"], reverse=True)
    return [{"username": u["username"], "points": u["points"]} for u in sorted_data]

