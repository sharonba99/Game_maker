from flask import request
from models import LeaderboardEntry
from .library import library_bp, j_ok, j_err


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

