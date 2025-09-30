from flask import Blueprint, request, jsonify
from sqlalchemy import func
from utils.db import db
from models import TriviaQuestion, QuizSession, LeaderboardEntry, Quiz
from datetime import datetime, timedelta

play_bp = Blueprint("play_bp", __name__)

def ok(data=None, status=200): return (jsonify({ "ok": True, "data": data }), status)
def err(msg, status=400):      return (jsonify({ "ok": False, "error": msg }), status)

# --- helpers ---
def _now(): return datetime.utcnow()

def _ensure_timer_initialized(session, default_limit=20):
    """Initialize timer for current question if not set."""
    if session.time_limit_sec is None:
        session.time_limit_sec = default_limit
    if session.question_started_at is None:
        session.question_started_at = _now()
        db.session.commit()

def _seconds_remaining(session):
    if session.question_started_at is None or session.time_limit_sec is None:
        return None
    elapsed = (_now() - session.question_started_at).total_seconds()
    remaining = int(max(0, session.time_limit_sec - elapsed))
    return remaining

@play_bp.post("/session/create")
def create_session():
    d = request.get_json(silent=True) or {}
    player = (d.get("player") or "").strip()
    quiz_id = d.get("quiz_id")
    topic   = (d.get("topic") or "").strip() or None
    limit   = int(d.get("limit") or 8)
    time_limit_sec = int(d.get("time_limit_sec") or 20)  # NEW: allow client to set

    if not player: return err("player is required", 400)

    if quiz_id:
        quiz = Quiz.query.get(int(quiz_id))
        if not quiz: return err("quiz not found", 404)
        ids = [int(x) for x in quiz.question_ids_csv.split(",")]
    else:
        q = TriviaQuestion.query
        if topic: q = q.filter(TriviaQuestion.topic == topic)
        ids = [r.id for r in q.order_by(func.random()).limit(limit).all()]

    if not ids: return err("no questions found", 404)

    s = QuizSession(
        player_name=player,
        quiz_id=quiz_id,
        question_ids_csv=','.join(map(str, ids)),
        time_limit_sec=time_limit_sec,
        question_started_at=None,   # will be set on first GET /question
    )
    db.session.add(s); db.session.commit()
    return ok({ "session_id": s.id, "count": len(ids), "time_limit_sec": time_limit_sec }, 201)

@play_bp.get("/session/<int:sid>/question")
def get_question(sid):
    s = QuizSession.query.get(sid)
    if not s: return err("session not found", 404)
    if s.is_finished: return err("session finished", 409)
    ids = [int(x) for x in s.question_ids_csv.split(",")]
    if s.current_index >= len(ids): return err("no more questions", 409)

    # initialize per-question timer if needed
    _ensure_timer_initialized(s)

    q = TriviaQuestion.query.get(ids[s.current_index])
    return ok({
        "index": s.current_index,
        "question_id": q.id,
        "text": q.text,
        "choices": {"A": q.choice_a, "B": q.choice_b, "C": q.choice_c, "D": q.choice_d},
        "topic": q.topic,
        "difficulty": q.difficulty,
        "time_limit_sec": s.time_limit_sec,
        "seconds_remaining": _seconds_remaining(s)
    })

@play_bp.post("/session/<int:sid>/answer")
def answer(sid):
    d = request.get_json(silent=True) or {}
    selected = (d.get("selected") or "").strip().upper()
    if selected not in ["A","B","C","D"]: return err("selected must be A/B/C/D", 400)

    s = QuizSession.query.get(sid)
    if not s: return err("session not found", 404)
    if s.is_finished: return err("session finished", 409)

    ids = [int(x) for x in s.question_ids_csv.split(",")]
    if s.current_index >= len(ids): return err("no more questions", 409)
    q = TriviaQuestion.query.get(ids[s.current_index])

    # difficulty-based scoring
    points_map = {"Easy": 50, "Medium": 100, "Hard": 200}
    base_points = points_map.get(q.difficulty, 100)

    # timer safeguard
    _ensure_timer_initialized(s)
    rem = _seconds_remaining(s)
    timed_out = (rem is not None and rem <= 0)

    correct = (selected == q.correct) and not timed_out

    if correct:
        # speed bonus: up to +50% when instantaneous; 0% when at last second
        bonus_factor = 1.0 + 0.5 * (rem / s.time_limit_sec) if s.time_limit_sec else 1.0
        awarded = int(round(base_points * bonus_factor))
    else:
        awarded = 0

    s.score += awarded

    # advance to next question: reset timer
    s.current_index += 1
    s.question_started_at = None  # will be re-init on next GET /question

    if s.current_index >= len(ids):
        s.is_finished = True
        db.session.add(LeaderboardEntry(player_name=s.player_name, score=s.score))

    db.session.commit()
    return ok({
        "correct": correct,
        "timed_out": timed_out,
        "awarded": awarded,
        "total_score": s.score,
        "difficulty": q.difficulty,
        "seconds_remaining": rem
    })

@play_bp.get("/leaderboard")
def leaderboard():
    rows = (LeaderboardEntry.query
            .order_by(LeaderboardEntry.score.desc(), LeaderboardEntry.created_at.asc())
            .limit(50).all())
    return ok([{"player": r.player_name, "score": r.score} for r in rows])
