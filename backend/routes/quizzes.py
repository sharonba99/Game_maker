from flask import request
from utils.db import db
from models import TriviaQuestion, Quiz, LeaderboardEntry
from .library import library_bp, j_ok, j_err, norm, ensure_answers


# ---------- Quizzes ----------
@library_bp.get("/quizzes")
def list_quizzes():
    topic = norm(request.args.get("topic")) or None
    q = Quiz.query
    if topic:
        q = q.filter(Quiz.topic == topic)
    rows = q.order_by(Quiz.id.desc()).all()
    data = [
        {
            "id": r.id,
            "title": r.title,
            "topic": r.topic,
            "difficulty": r.difficulty,
            "count": len(r.questions),
        }
        for r in rows
    ]
    return j_ok(data)


@library_bp.get("/quizzes/<int:quiz_id>")
def get_quiz(quiz_id: int):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return j_err("not_found", f"quiz {quiz_id} not found", 404)
    data = {
        "id": quiz.id,
        "title": quiz.title,
        "topic": quiz.topic,
        "difficulty": quiz.difficulty,
        "count": len(quiz.questions),
        "questions": [
            {
                "id": q.id,
                "question": q.question,
                "topic": q.topic,
                "difficulty": q.difficulty,
                "answers": q.answers,
            }
            for q in quiz.questions
        ],
    }
    return j_ok(data)


@library_bp.post("/quizzes")
def create_quiz():
    b = request.get_json(silent=True) or {}
    title = norm(b.get("title"))
    topic = norm(b.get("topic"))
    difficulty = norm(b.get("difficulty")) or None
    if not title or not topic:
        return j_err("bad_request", "title & topic are required", 400)
    row = Quiz(title=title, topic=topic, difficulty=difficulty)
    db.session.add(row)
    db.session.commit()
    return j_ok({"id": row.id}, 201)


@library_bp.post("/import")
def bulk_import():
    body = request.get_json(silent=True) or {}
    quizzes = body.get("quizzes", [])
    if not quizzes or not isinstance(quizzes, list):
        return j_err("bad_request", "quizzes must be a non-empty array", 400)
    created = []
    try:
        for qz in quizzes:
            title = norm(qz.get("title"))
            topic = norm(qz.get("topic"))
            difficulty = norm(qz.get("difficulty")) or None
            questions = qz.get("questions", [])
            if not title or not topic:
                return j_err("bad_request", "title & topic required for each quiz", 400)
            quiz = Quiz(title=title, topic=topic, difficulty=difficulty)
            db.session.add(quiz)
            db.session.flush()
            for q in questions:
                question_text = norm(q.get("question"))
                q_diff = norm(q.get("difficulty")) or None
                answers = q.get("answers")
                ok, err = ensure_answers(answers)
                if not question_text or not ok:
                    return j_err("bad_request", err or "invalid question/answers", 400)
                tq = TriviaQuestion(
                    question=question_text,
                    topic=topic,
                    difficulty=q_diff,
                    answers=answers,
                    quiz_id=quiz.id
                )
                db.session.add(tq)
            created.append({"quiz_id": quiz.id, "title": quiz.title, "count": len(questions)})
        db.session.commit()
        return j_ok({"created": created}, 201)
    except Exception as e:
        db.session.rollback()
        return j_err("server_error", str(e), 500)


@library_bp.delete("/quizzes/<int:quiz_id>")
def delete_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return j_err("not_found", f"Quiz with id {quiz_id} not found", 404)
    db.session.delete(quiz)
    db.session.commit()
    return j_ok({"message": f"Quiz {quiz_id} and all its questions have been deleted"})


@library_bp.delete("/topics/<string:topic>")
def delete_topic(topic):
    topic = topic.strip()
    if not topic:
        return j_err("bad_request", "Topic is required", 400)
    quizzes = Quiz.query.filter_by(topic=topic).all()
    quiz_ids = [q.id for q in quizzes]
    if quiz_ids:
        LeaderboardEntry.query.filter(LeaderboardEntry.quiz_id.in_(quiz_ids)).delete(synchronize_session=False)
    Quiz.query.filter_by(topic=topic).delete(synchronize_session=False)
    TriviaQuestion.query.filter_by(topic=topic).delete(synchronize_session=False)
    db.session.commit()
    return j_ok({"message": f"Deleted topic '{topic}' along with {len(quizzes)} quizzes and all related questions."})


@library_bp.delete("/leaderboard")
def delete_leaderboard():
    deleted = LeaderboardEntry.query.delete(synchronize_session=False)
    db.session.commit()
    return j_ok({"message": f"Deleted {deleted} leaderboard entries."})
