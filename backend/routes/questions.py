from flask import request
from utils.db import db
from models import TriviaQuestion, Quiz
from .library import library_bp, j_ok, j_err, norm, ensure_answers


@library_bp.post("/questions")
def add_question():
    b = request.get_json(silent=True) or {}
    question = norm(b.get("question"))
    difficulty = norm(b.get("difficulty")) or None
    answers = b.get("answers")
    quiz_id = b.get("quiz_id")
    if not quiz_id:
        return j_err("bad_request", "quiz_id is required", 400)
    ok, err = ensure_answers(answers)
    if not question or not ok:
        return j_err("bad_request", err or "question and answers[4] are required", 400)
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return j_err("not_found", f"quiz {quiz_id} not found", 404)
    dup = TriviaQuestion.query.filter_by(question=question, quiz_id=quiz_id).first()
    if dup:
        return j_err("duplicate", "question already exists in this quiz", 409)
    row = TriviaQuestion(
        question=question,
        topic=quiz.topic,
        difficulty=difficulty,
        answers=answers,
        quiz_id=quiz_id,
    )
    db.session.add(row)
    db.session.commit()
    return j_ok({"id": row.id}, 201)