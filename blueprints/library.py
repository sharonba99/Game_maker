import random
from flask import Blueprint, request, jsonify
from sqlalchemy import func
from utils.db import db
from models import (
    TriviaQuestion,
    Quiz,
    QuizSession,
    QuizAnswerLog,
    LeaderboardEntry,
)

library_bp = Blueprint("library_bp", __name__)

# ---------- helpers ----------
def j_ok(data=None, status=200):
    return jsonify({"ok": True, "data": data}), status

def j_err(code, msg, status=400):
    return jsonify({"ok": False, "error": {"code": code, "message": msg}}), status

def norm(x): return (x or "").strip()

def ensure_answers(arr):
    if not isinstance(arr, list) or len(arr) != 4:
        return False, "answers must be an array of 4 items"
    if any(not norm(a) for a in arr):
        return False, "answers must not contain empty texts"
    return True, None

# ---------- Questions (Library) ----------
@library_bp.get("/questions")
def list_questions():
    rows = TriviaQuestion.query.order_by(TriviaQuestion.id).all()
    data = [{
        "id": r.id,
        "question": r.question,
        "topic": r.topic,
        "difficulty": r.difficulty
    } for r in rows]
    return j_ok(data)

@library_bp.post("/add")
def add_question():
    """
    JSON:
    {
      "question": "2+2?",
      "topic": "Math",
      "difficulty": "easy",
      "answers": ["4","5","3","22"]  # first is correct
    }
    """
    try:
        body = request.get_json(silent=True) or {}
        question = norm(body.get("question"))
        topic = norm(body.get("topic")) or None
        difficulty = norm(body.get("difficulty")) or None
        answers = body.get("answers")

        ok, err = ensure_answers(answers)
        if not question or not ok:
            return j_err("bad_request", err or "question and answers[4] are required", 400)

        dup = TriviaQuestion.query.filter_by(question=question, topic=topic).first()
        if dup:
            return j_err("duplicate", "question already exists", 409)

        row = TriviaQuestion(question=question, topic=topic, difficulty=difficulty, answers=answers)
        db.session.add(row); db.session.commit()
        return j_ok({"id": row.id}, 201)
    except Exception as e:
        db.session.rollback()
        return j_err("server_error", str(e), 500)

@library_bp.get("/question/<int:item_id>")
def get_question_public(item_id: int):
    r = TriviaQuestion.query.get(item_id)
    if not r:
        return j_err("not_found", "question not found", 404)
    options = list(r.answers); random.shuffle(options)
    return j_ok({
        "id": r.id,
        "question": r.question,
        "topic": r.topic,
        "difficulty": r.difficulty,
        "options": options
    })

# ---------- Topics ----------
@library_bp.get("/topics")
def topics():
    rows = db.session.query(TriviaQuestion.topic) \
        .filter(TriviaQuestion.topic.isnot(None)) \
        .group_by(TriviaQuestion.topic).all()
    return j_ok([t[0] for t in rows])

# ---------- Quizzes ----------
@library_bp.post("/quizzes")
def create_quiz():
    """
    JSON:
    {
      "title": "Math — Easy Set A",
      "topic": "Math",
      "difficulty": "easy",
      "question_ids": [1,5,7,9],  # optional
      "count": 5                  # used if question_ids empty
    }
    """
    b = request.get_json(silent=True) or {}
    title = norm(b.get("title"))
    topic = norm(b.get("topic"))
    difficulty = norm(b.get("difficulty")) or None
    qids = b.get("question_ids") or []
    count = int(b.get("count") or 5)

    if not title or not topic:
        return j_err("bad_request", "title & topic are required", 400)

    if not qids:
        qs = TriviaQuestion.query.filter(TriviaQuestion.topic == topic)
        if difficulty:
            qs = qs.filter(TriviaQuestion.difficulty == difficulty)
        allq = qs.all()
        if not allq:
            return j_err("no_questions", "no questions for this topic", 404)
        count = max(1, min(count, len(allq)))
        qids = [q.id for q in random.sample(allq, count)]

    row = Quiz(title=title, topic=topic, difficulty=difficulty, question_ids=qids)
    db.session.add(row); db.session.commit()
    return j_ok({"id": row.id}, 201)

@library_bp.get("/quizzes")
def list_quizzes():
    topic = norm(request.args.get("topic")) or None
    q = Quiz.query
    if topic:
        q = q.filter(Quiz.topic == topic)
    rows = q.order_by(Quiz.id.desc()).all()
    data = [{
        "id": r.id,
        "title": r.title,
        "topic": r.topic,
        "difficulty": r.difficulty,
        "count": len(r.question_ids)
    } for r in rows]
    return j_ok(data)

# ---------- Session (game flow) ----------
@library_bp.post("/session/create")
def session_create():
    """
    JSON: { "player_name": "neomi", "quiz_id": 12 }
    """
    b = request.get_json(silent=True) or {}
    player = norm(b.get("player_name")) or "guest"
    quiz_id = b.get("quiz_id")
    if not quiz_id:
        return j_err("bad_request", "quiz_id is required", 400)

    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return j_err("not_found", "quiz not found", 404)

    s = QuizSession(
        quiz_id=quiz.id,
        player_name=player,
        score=0,
        total_questions=len(quiz.question_ids),
        current_index=0
    )
    db.session.add(s); db.session.commit()
    return j_ok({"session_id": s.id})

@library_bp.get("/session/<int:sid>/current")
def session_current(sid: int):
    s = QuizSession.query.get(sid)
    if not s: return j_err("not_found", "session not found", 404)
    quiz = Quiz.query.get(s.quiz_id)

    if s.current_index >= len(quiz.question_ids):
        return j_ok({"finished": True, "score": s.score})

    qid = quiz.question_ids[s.current_index]
    q = TriviaQuestion.query.get(qid)
    options = list(q.answers); random.shuffle(options)

    return j_ok({
        "finished": False,
        "question_id": q.id,
        "question": q.question,
        "options": options,
        "index": s.current_index,
        "total": s.total_questions
    })

@library_bp.post("/session/<int:sid>/answer")
def session_answer(sid: int):
    """
    JSON: { "answer": "Paris", "client_ms": 1800 }
    Scoring: correct → max(100, 1000 - client_ms/2); wrong → 0
    """
    b = request.get_json(silent=True) or {}
    answer = norm(b.get("answer"))
    client_ms = int(b.get("client_ms") or 0)

    s = QuizSession.query.get(sid)
    if not s: return j_err("not_found", "session not found", 404)
    quiz = Quiz.query.get(s.quiz_id)

    if s.current_index >= len(quiz.question_ids):
        return j_ok({"finished": True, "score": s.score})

    qid = quiz.question_ids[s.current_index]
    q = TriviaQuestion.query.get(qid)

    is_correct = (answer.lower() == q.answers[0].strip().lower())
    awarded = 0
    if is_correct:
        awarded = max(100, 1000 - (client_ms // 2))
        s.score += awarded

    log = QuizAnswerLog(
        session_id=s.id,
        question_id=q.id,
        is_correct=is_correct,
        client_ms=client_ms,
        awarded=awarded
    )
    db.session.add(log)

    s.current_index += 1
    finished = s.current_index >= len(quiz.question_ids)

    if finished:
        lb = LeaderboardEntry(quiz_id=quiz.id, player_name=s.player_name, score=s.score)
        db.session.add(lb)

    db.session.commit()

    if finished:
        return j_ok({"finished": True, "score": s.score})

    next_q = TriviaQuestion.query.get(quiz.question_ids[s.current_index])
    opts = list(next_q.answers); random.shuffle(opts)
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

    rows = LeaderboardEntry.query.filter_by(quiz_id=quiz_id) \
        .order_by(LeaderboardEntry.score.desc(), LeaderboardEntry.id.asc()) \
        .limit(10).all()

    top = [{"player_name": r.player_name, "score": r.score} for r in rows]
    return j_ok({"top": top})



 