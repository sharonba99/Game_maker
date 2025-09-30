import random
from flask import Blueprint, request, jsonify
from sqlalchemy import func
from utils.db import db
from models import TriviaQuestion, Quiz, QuizSession, QuizAnswerLog, LeaderboardEntry

library_bp = Blueprint("library_bp", __name__)

# ---------- helpers ----------
def j_ok(data=None, status=200):
    return jsonify({"ok": True, "data": data}), status

def j_err(code, msg, status=400):
    return jsonify({"ok": False, "error": {"code": code, "message": msg}}), status

def norm(x): 
    return (x or "").strip()

def ensure_answers(arr):
    if not isinstance(arr, list) or len(arr) != 4:
        return False, "answers must be an array of 4 items"
    if any(not norm(a) for a in arr):
        return False, "answers must not contain empty texts"
    return True, None

def get_session_or_error(sid: int):
    s = QuizSession.query.get(sid)
    if not s:
        return None, j_err("not_found", "session not found", 404)
    return s, None

def get_quiz_and_questions(quiz_id: int):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return None, None, j_err("not_found", "quiz not found", 404)
    questions = quiz.questions
    if not questions:
        return quiz, [], j_err("empty_quiz", "quiz has no questions", 400)
    return quiz, questions, None

# ---------- Topics ----------
@library_bp.get("/topics")
def topics():
    rows = (
        db.session.query(TriviaQuestion.topic)
        .filter(TriviaQuestion.topic.isnot(None))
        .group_by(TriviaQuestion.topic)
        .all()
    )
    return j_ok([t[0] for t in rows])

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

# ---------- Game session ----------
@library_bp.post("/session/create")
def session_create():
    b = request.get_json(silent=True) or {}
    player = norm(b.get("player_name")) or "guest"
    quiz_id = b.get("quiz_id")
    if not quiz_id:
        return j_err("bad_request", "quiz_id is required", 400)
    quiz, questions, err = get_quiz_and_questions(quiz_id)
    if err:
        return err
    s = QuizSession(
        quiz_id=quiz.id,
        player_name=player,
        score=0,
        total_questions=len(questions),
        current_index=0,
    )
    db.session.add(s)
    db.session.commit()
    return j_ok({"session_id": s.id})

@library_bp.get("/session/<int:sid>/current")
def session_current(sid: int):
    s, err = get_session_or_error(sid)
    if err:
        return err
    quiz, questions, err = get_quiz_and_questions(s.quiz_id)
    if err:
        return err
    if s.current_index >= len(questions):
        return j_ok({"finished": True, "score": s.score})
    q = questions[s.current_index]
    options = list(q.answers)
    random.shuffle(options)
    return j_ok({
        "finished": False,
        "question_id": q.id,
        "question": q.question,
        "options": options,
        "index": s.current_index,
        "total": s.total_questions,
    })

@library_bp.post("/session/<int:sid>/answer")
def session_answer(sid: int):
    b = request.get_json(silent=True) or {}
    answer = norm(b.get("answer"))
    client_ms = int(b.get("client_ms") or 0)
    s, err = get_session_or_error(sid)
    if err:
        return err
    quiz, questions, err = get_quiz_and_questions(s.quiz_id)
    if err:
        return err
    if s.current_index >= len(questions):
        return j_ok({"finished": True, "score": s.score})
    q = questions[s.current_index]
    is_correct = (answer.lower() == q.answers[0].strip().lower())
    awarded = max(100, 1000 - (client_ms // 2)) if is_correct else 0
    if is_correct:
        s.score += awarded
    log = QuizAnswerLog(
        session_id=s.id,
        question_id=q.id,
        is_correct=is_correct,
        client_ms=client_ms,
        awarded=awarded,
    )
    db.session.add(log)
    s.current_index += 1
    finished = s.current_index >= len(questions)
    if finished:
        db.session.flush()
        total_ms = db.session.query(
            func.coalesce(func.sum(QuizAnswerLog.client_ms), 0)
        ).filter(QuizAnswerLog.session_id == s.id).scalar()
        lb = LeaderboardEntry(
            quiz_id=quiz.id,
            user_id=getattr(s, "player_user_id", None),
            player_name=s.player_name,
            score=s.score,
            duration_ms=int(total_ms or 0),
        )
        db.session.add(lb)
    db.session.commit()
    if finished:
        return j_ok({"finished": True, "score": s.score})
    next_q = questions[s.current_index]
    opts = list(next_q.answers)
    random.shuffle(opts)
    return j_ok({
        "finished": False,
        "score": s.score,
        "next": {
            "question_id": next_q.id,
            "question": next_q.question,
            "options": opts,
            "index": s.current_index,
            "total": s.total_questions
        }
    })

# ---------- Leaderboard ----------
@library_bp.get("/leaderboard")
def leaderboard():
    quiz_id = request.args.get("quiz_id", type=int)
    if not quiz_id:
        return j_err("bad_request", "quiz_id is required", 400)
    rows = (LeaderboardEntry.query
        .filter_by(quiz_id=quiz_id)
        .order_by(
            LeaderboardEntry.score.desc(),
            LeaderboardEntry.duration_ms.asc().nullslast(),
            LeaderboardEntry.id.asc()
        )
        .limit(10)
        .all())
    return j_ok({"top": [
        {
            "player_name": r.player_name,
            "score": r.score,
            "duration_ms": r.duration_ms or 0,
            "created_at": r.created_at.isoformat()
        } for r in rows
    ]})
