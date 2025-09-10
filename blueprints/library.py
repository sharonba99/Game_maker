from flask import Blueprint, request, jsonify
from sqlalchemy import func
from utils.db import db
from models import TriviaQuestion

library_bp = Blueprint("library_bp", __name__)

# ---------- helpers ----------

def j_ok(data=None, status=200):
    return jsonify({"ok": True, "data": data}), status

def j_err(code: str, message: str, status=400):
    return jsonify({"ok": False, "error": {"code": code, "message": message}}), status

def normalize(text: str | None) -> str:
    return (text or "").strip()

def normalize_key(text: str | None) -> str:
    return (text or "").strip().lower()

# ---------- routes ----------

@library_bp.get("/")
def list_questions():
    """List questions with optional pagination: ?limit=20&offset=0"""
    try:
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))
        limit = max(1, min(limit, 200)) 

        q = TriviaQuestion.query.order_by(TriviaQuestion.id)
        total = q.count()
        rows = q.offset(offset).limit(limit).all()

        data = [
            {"id": r.id, "question": r.question, "answer": r.answer, "topic": r.topic}
            for r in rows
        ]
        return j_ok({"items": data, "total": total, "limit": limit, "offset": offset})
    except Exception as e:
        return j_err("server_error", str(e), 500)

@library_bp.get("/<int:item_id>")
def get_question(item_id: int):
    """Get single question by id"""
    row = TriviaQuestion.query.get(item_id)
    if not row:
        return j_err("not_found", "question not found", 404)
    return j_ok({"id": row.id, "question": row.question, "answer": row.answer, "topic": row.topic})

@library_bp.post("/add")
def add_question():
    """
    Add a single question.
    JSON: { "question": "...", "answer": "...", "topic": "Math" }
    """
    try:
        body = request.get_json(silent=True) or {}
        question = normalize(body.get("question"))
        answer   = normalize(body.get("answer"))
        topic    = normalize(body.get("topic")) or None

        if not question or not answer:
            return j_err("bad_request", "question and answer are required", 400)

        exists = (
            db.session.query(TriviaQuestion.id)
            .filter(
                func.lower(TriviaQuestion.question) == normalize_key(question),
                (TriviaQuestion.topic == topic) | (topic is None and TriviaQuestion.topic.is_(None))
            )
            .first()
        )
        if exists:
            return j_err("duplicate", "question already exists", 409)

        row = TriviaQuestion(question=question, answer=answer, topic=topic)
        db.session.add(row)
        db.session.commit()
        return j_ok({"id": row.id}, 201)

    except Exception as e:
        db.session.rollback()
        return j_err("server_error", str(e), 500)

@library_bp.post("/bulk_add")
def bulk_add():
    """
    Add multiple questions at once.
    JSON: { "items": [ {question, answer, topic?}, ... ] }
    Returns counts and ids of inserted items; duplicates are skipped.
    """
    try:
        body = request.get_json(silent=True) or {}
        items = body.get("items") or []
        if not isinstance(items, list) or not items:
            return j_err("bad_request", "items array is required", 400)

        inserted = []
        skipped = []

        for i, it in enumerate(items):
            q_text = normalize(it.get("question"))
            a_text = normalize(it.get("answer"))
            t_text = normalize(it.get("topic")) or None

            if not q_text or not a_text:
                skipped.append({"index": i, "reason": "missing fields"})
                continue

            dup = (
                db.session.query(TriviaQuestion.id)
                .filter(
                    func.lower(TriviaQuestion.question) == normalize_key(q_text),
                    (TriviaQuestion.topic == t_text) | (t_text is None and TriviaQuestion.topic.is_(None))
                )
                .first()
            )
            if dup:
                skipped.append({"index": i, "reason": "duplicate"})
                continue

            row = TriviaQuestion(question=q_text, answer=a_text, topic=t_text)
            db.session.add(row)
            inserted.append(row)

        db.session.commit()
        return j_ok({
            "inserted_ids": [r.id for r in inserted],
            "inserted": len(inserted),
            "skipped": skipped,
            "total_received": len(items)
        }, 201)

    except Exception as e:
        db.session.rollback()
        return j_err("server_error", str(e), 500)

@library_bp.put("/<int:item_id>")
def update_question(item_id: int):
    """
    Update an existing question.
    JSON (partial allowed): { "question": "...", "answer": "...", "topic": "..." }
    """
    try:
        row = TriviaQuestion.query.get(item_id)
        if not row:
            return j_err("not_found", "question not found", 404)

        body = request.get_json(silent=True) or {}

        new_q = normalize(body.get("question")) if "question" in body else row.question
        new_a = normalize(body.get("answer"))   if "answer"   in body else row.answer
        new_t = normalize(body.get("topic")) or None if "topic" in body else row.topic

        if not new_q or not new_a:
            return j_err("bad_request", "question and answer are required", 400)

        # בדיקת כפילות אם השתנה הטקסט/נושא
        if (normalize_key(new_q) != normalize_key(row.question)) or ((new_t or "") != (row.topic or "")):
            dup = (
                db.session.query(TriviaQuestion.id)
                .filter(
                    TriviaQuestion.id != row.id,
                    func.lower(TriviaQuestion.question) == normalize_key(new_q),
                    (TriviaQuestion.topic == new_t) | (new_t is None and TriviaQuestion.topic.is_(None))
                )
                .first()
            )
            if dup:
                return j_err("duplicate", "question already exists", 409)

        row.question = new_q
        row.answer   = new_a
        row.topic    = new_t
        db.session.commit()

        return j_ok({"id": row.id})

    except Exception as e:
        db.session.rollback()
        return j_err("server_error", str(e), 500)

@library_bp.delete("/<int:item_id>")
def delete_question(item_id: int):
    """Delete question by id"""
    try:
        row = TriviaQuestion.query.get(item_id)
        if not row:
            return j_err("not_found", "question not found", 404)
        db.session.delete(row)
        db.session.commit()
        return j_ok({"id": item_id})
    except Exception as e:
        db.session.rollback()
        return j_err("server_error", str(e), 500)

@library_bp.get("/search")
def search_questions():
    """
    Search/filter with pagination:
    /library/search?q=capital&topic=Geography&limit=20&offset=0
    """
    try:
        q_text = normalize(request.args.get("q"))
        topic  = normalize(request.args.get("topic")) or None
        limit  = max(1, min(int(request.args.get("limit", 50)), 200))
        offset = max(0, int(request.args.get("offset", 0)))

        query = TriviaQuestion.query
        if q_text:
            like = f"%{q_text}%"
            query = query.filter(TriviaQuestion.question.ilike(like))
        if topic:
            query = query.filter(TriviaQuestion.topic == topic)

        total = query.count()
        rows = query.order_by(TriviaQuestion.id).offset(offset).limit(limit).all()

        data = [
            {"id": r.id, "question": r.question, "answer": r.answer, "topic": r.topic}
            for r in rows
        ]
        return j_ok({"items": data, "total": total, "limit": limit, "offset": offset})
    except Exception as e:
        return j_err("server_error", str(e), 500)


 