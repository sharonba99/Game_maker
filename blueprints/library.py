import random
from flask import Blueprint, request, jsonify
from sqlalchemy import func
from utils.db import db
from models import Quiz, QuizSession, QuizAnswerLog, LeaderboardEntry

library_bp = Blueprint("library_bp", __name__)

# ----------------- Helpers -----------------
def j_ok(data=None, status=200):
    return jsonify({"ok": True, "data": data}), status

def j_err(code, msg, status=400):
    return jsonify({"ok": False, "error": {"code": code, "message": msg}}), status


def norm(text: str | None) -> str:
    """Normalize text by stripping spaces or returning empty string if None"""
    return (text or "").strip()

def get_session_or_error(sid: int):
    """Fetch a session by id or return error response"""
    s = QuizSession.query.get(sid)
    if not s:
        return None, j_err("not_found", "session not found", 404)
    return s, None

def get_quiz_and_questions(quiz_id: int):
    """Fetch quiz and its questions or return error response"""
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return None, None, j_err("not_found", "quiz not found", 404)

    questions = quiz.questions
    if not questions:
        return quiz, [], j_err("empty_quiz", "quiz has no questions", 400)

    return quiz, questions, None

# ----------------- Game session routes -----------------

@library_bp.post("/session/create")
def session_create():
    """
    Create a new game session
    Input JSON: { "player_name": "neomi", "quiz_id": 12 }
    """
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
    """
    Get the current question for a session
    """
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
    """
    Submit an answer for the current question
    Input JSON: { "answer": "Paris", "client_ms": 1800 }
    Scoring: correct -> max(100, 1000 - client_ms/2), wrong -> 0
    """
    b = request.get_json(silent=True) or {}
    answer = norm(b.get("answer"))
    client_ms = int(b.get("client_ms") or 0)

    s, err = get_session_or_error(sid)
    if err:
        return err

    quiz, questions, err = get_quiz_and_questions(s.quiz_id)
    if err:
        return err

    # if the game is already finished
    if s.current_index >= len(questions):
        return j_ok({"finished": True, "score": s.score})

    # current question
    q = questions[s.current_index]

    # check answer
    is_correct = (answer.lower() == q.answers[0].strip().lower())
    awarded = max(100, 1000 - (client_ms // 2)) if is_correct else 0
    if is_correct:
        s.score += awarded

    # answer log – note: there is no duration_ms in the model, only client_ms
    log = QuizAnswerLog(
        session_id=s.id,
        question_id=q.id,
        is_correct=is_correct,
        client_ms=client_ms,
        awarded=awarded,
    )
    db.session.add(log)

    # go to the next question
    s.current_index += 1
    finished = s.current_index >= len(questions)

    if finished:
        # ensure the current question's QuizAnswerLog is in the buffer before aggregation
        db.session.flush()

        # sum of all answer times (ms) for this session
        total_ms = db.session.query(
            func.coalesce(func.sum(QuizAnswerLog.client_ms), 0)
        ).filter(QuizAnswerLog.session_id == s.id).scalar()

        lb = LeaderboardEntry(
            quiz_id=quiz.id,
            user_id=getattr(s, "player_user_id", None),
            player_name=s.player_name,
            score=s.score,
            duration_ms=int(total_ms or 0),  # <<< stored in leaderboard
        )
        db.session.add(lb)

    db.session.commit()

    if finished:
        return j_ok({"finished": True, "score": s.score})

    # prepare the next question
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
