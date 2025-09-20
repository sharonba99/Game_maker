from flask import Blueprint, request, jsonify
from utils.db import db
from models import TriviaQuestion, Quiz

library_bp = Blueprint("library_bp", __name__)

def ok(data=None, status=200):
    return jsonify({"ok": True, "data": data}), status

def err(msg, status=400):
    return jsonify({"ok": False, "error": msg}), status

#Add new multiple-choice question
@library_bp.post("/library/questions/add")
def add_question():
    d = request.get_json(silent=True) or {}
    req = ["text", "A", "B", "C", "D", "correct"]
    for k in req:
        if not d.get(k):
            return err(f"{k} is required", 400)

    q = TriviaQuestion(
        topic=d.get("topic"),
        text=d["text"],
        choice_a=d["A"],
        choice_b=d["B"],
        choice_c=d["C"],
        choice_d=d["D"],
        correct=d["correct"],
        difficulty=d.get("difficulty", "Easy")  # default Easy
    )
    db.session.add(q)
    db.session.commit()
    return ok({"id": q.id}, 201)

#List questions
@library_bp.get("/library/questions")
def list_questions():
    rows = TriviaQuestion.query.limit(50).all()
    return ok([{
        "id": r.id,
        "topic": r.topic,
        "text": r.text,
        "A": r.choice_a,
        "B": r.choice_b,
        "C": r.choice_c,
        "D": r.choice_d,
        "correct": r.correct,
        "difficulty": r.difficulty
    } for r in rows])

#Create a quiz from question IDs or by topic
@library_bp.post("/library/quizzes/create")
def create_quiz():
    d = request.get_json(silent=True) or {}
    name = d.get("name")
    if not name:
        return err("name is required", 400)

    ids = d.get("question_ids") or []
    topic = d.get("topic")

    if not ids and not topic:
        return err("either question_ids or topic required", 400)

    if ids:
        ids_str = ",".join(str(i) for i in ids)
    else:
        # select by topic
        limit = int(d.get("limit") or 8)
        qs = TriviaQuestion.query.filter(TriviaQuestion.topic == topic).limit(limit).all()
        ids_str = ",".join(str(q.id) for q in qs)

    qz = Quiz(name=name, topic=topic, question_ids_csv=ids_str)
    db.session.add(qz)
    db.session.commit()
    return ok({"quiz_id": qz.id, "count": len(ids_str.split(","))}, 201)

#List quizzes
@library_bp.get("/library/quizzes")
def list_quizzes():
    rows = Quiz.query.limit(50).all()
    return ok([{
        "id": r.id,
        "name": r.name,
        "topic": r.topic,
        "count": len(r.question_ids_csv.split(",")) if r.question_ids_csv else 0
    } for r in rows])
