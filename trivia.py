from flask import Flask, Blueprint, request, jsonify
from utils.utils import trivia

current_id = 1
trivia_bp = Blueprint('trivia_bp', __name__)

@trivia_bp.get('/')
def show_trivia():
    return trivia

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


@trivia_bp.get('/question/<int:id>')
def get_question(id):
    for question in trivia:
        if question.get('id') == id:
            return question
    return jsonify({'status': 'not found'}), 404