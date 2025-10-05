from utils.db import db
from models import TriviaQuestion
from .library import library_bp, j_ok


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