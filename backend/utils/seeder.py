import json
from pathlib import Path
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError
from models import Quiz, TriviaQuestion
from utils.db import db

def auto_seed():
    insp = inspect(db.engine)

    if insp.has_table("quiz") and insp.has_table("trivia_question"):
        try:
            if db.session.query(Quiz).count() == 0:
                data_path = Path(__file__).resolve().parent.parent / "data" / "seed_quizzes.json"
                if data_path.exists():
                    data = json.loads(data_path.read_text(encoding="utf-8"))
                    created = 0
                    for qz in data.get("quizzes", []):
                        title = (qz.get("title") or "").strip()
                        topic = (qz.get("topic") or "").strip()
                        difficulty = (qz.get("difficulty") or None) or None
                        questions = qz.get("questions", [])
                        if not title or not topic:
                            continue
                        quiz = Quiz(title=title, topic=topic, difficulty=difficulty)
                        db.session.add(quiz)
                        db.session.flush()
                        for q in questions:
                            question_text = (q.get("question") or "").strip()
                            q_diff = (q.get("difficulty") or None) or None
                            answers = q.get("answers", [])
                            if (
                                isinstance(answers, list) and len(answers) == 4
                                and all((a or "").strip() for a in answers) and question_text
                            ):
                                db.session.add(TriviaQuestion(
                                    question=question_text, topic=topic,
                                    difficulty=q_diff, answers=answers, quiz_id=quiz.id
                                ))
                        created += 1
                    db.session.commit()
                    print(f">>> Default quizzes seeded ({created}).")
        except OperationalError:
            db.session.rollback()
            print(">>> Skipping auto-seed (tables not ready).")
    else:
        print(">>> Tables not ready yet; skipping auto-seed.")
