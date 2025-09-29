import random
from flask import Blueprint, request, jsonify
from utils.db import db
from models import TriviaQuestion, Quiz, QuizSession, QuizAnswerLog, LeaderboardEntry
from sqlalchemy import func

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
    """
    JSON:
    {
      "title": "Math — Easy Set A",
      "topic": "Math",
      "difficulty": "easy"   # אופציונלי
    }
    """
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
    """
    JSON:
    {
      "quiz_id": 1,
      "question": "2+2?",
      "difficulty": "easy",    # אופציונלי
      "answers": ["4","5","3","22"]  # הראשונה נכונה
    }
    """
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

# ---------- Game session ----------
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

    questions = quiz.questions
    if not questions:
        return j_err("empty_quiz", "quiz has no questions", 400)

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
    s = QuizSession.query.get(sid)
    if not s:
        return j_err("not_found", "session not found", 404)

    quiz = Quiz.query.get(s.quiz_id)
    questions = quiz.questions

    if s.current_index >= len(questions):
        return j_ok({"finished": True, "score": s.score})

    q = questions[s.current_index]
    options = list(q.answers)
    random.shuffle(options)

    return j_ok(
        {
            "finished": False,
            "question_id": q.id,
            "question": q.question,
            "options": options,
            "index": s.current_index,
            "total": s.total_questions,
        }
    )

@library_bp.post("/session/<int:sid>/answer")
def session_answer(sid: int):
    """
    JSON: { "answer": "Paris", "client_ms": 1800 }
    ניקוד: תשובה נכונה -> max(100, 1000 - client_ms/2); שגויה -> 0
    """
    b = request.get_json(silent=True) or {}
    answer = norm(b.get("answer"))
    client_ms = int(b.get("client_ms") or 0)  # זה הזמן היחיד שאנחנו שומרים בלוג

    s = QuizSession.query.get(sid)
    if not s:
        return j_err("not_found", "session not found", 404)

    quiz = Quiz.query.get(s.quiz_id)
    questions = quiz.questions

    # אם כבר סיימנו
    if s.current_index >= len(questions):
        return j_ok({"finished": True, "score": s.score})

    # השאלה הנוכחית
    q = questions[s.current_index]

    # בדיקת תשובה
    is_correct = (answer.lower() == q.answers[0].strip().lower())
    awarded = max(100, 1000 - (client_ms // 2)) if is_correct else 0
    if is_correct:
        s.score += awarded

    # לוג תשובה – שימי לב: אין duration_ms במודל, רק client_ms
    log = QuizAnswerLog(
        session_id=s.id,
        question_id=q.id,
        is_correct=is_correct,
        client_ms=client_ms,
        awarded=awarded,
    )
    db.session.add(log)

    # התקדמות לשאלה הבאה
    s.current_index += 1
    finished = s.current_index >= len(questions)

    # אם סיימנו – מכניסים ללידרבורד (אין duration_ms גם פה)
       # התקדמות לשאלה הבאה
    s.current_index += 1
    finished = s.current_index >= len(questions)

    if finished:
        # נוודא שה-QuizAnswerLog של השאלה הנוכחית נמצא בבאפר לפני הסכימה
        db.session.flush()

        # סכום כל זמני התשובה (ms) של הסשן הזה
        total_ms = db.session.query(
            func.coalesce(func.sum(QuizAnswerLog.client_ms), 0)
        ).filter(QuizAnswerLog.session_id == s.id).scalar()

        lb = LeaderboardEntry(
            quiz_id=quiz.id,
            user_id=getattr(s, "player_user_id", None),
            player_name=s.player_name,
            score=s.score,
            duration_ms=int(total_ms or 0),  # <<< נשמר בדירוג
        )
        db.session.add(lb)

    db.session.commit()

    if finished:
        return j_ok({"finished": True, "score": s.score})


    # להכין את השאלה הבאה
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
        .order_by(LeaderboardEntry.score.desc(),
                  LeaderboardEntry.duration_ms.asc().nullslast(),
                  LeaderboardEntry.id.asc())
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


