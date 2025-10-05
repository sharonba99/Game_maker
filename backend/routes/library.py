from flask import Blueprint, request
from sqlalchemy import func
import random

from utils.db import db
from utils.helpers import j_ok, j_err, norm, ensure_answers
from models import TriviaQuestion, Quiz, QuizSession, QuizAnswerLog, LeaderboardEntry

library_bp = Blueprint("library_bp", __name__)

# ---------- helpers ----------
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


