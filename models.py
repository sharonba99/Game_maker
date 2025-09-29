from utils.db import db
from sqlalchemy.dialects.sqlite import JSON
from datetime import datetime

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

class Quiz(db.Model):
    __tablename__ = "quiz"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    topic = db.Column(db.String, nullable=False)
    difficulty = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    owner_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    questions = db.relationship("TriviaQuestion", back_populates="quiz", cascade="all, delete-orphan")

class TriviaQuestion(db.Model):
    __tablename__ = "trivia_question"
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String, nullable=False)
    topic = db.Column(db.String, nullable=True)
    difficulty = db.Column(db.String, nullable=True)
    answers = db.Column(JSON, nullable=False)  # ["correct","w1","w2","w3"]
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    quiz = db.relationship("Quiz", back_populates="questions")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class QuizSession(db.Model):
    __tablename__ = "quiz_session"
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    player_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    player_name = db.Column(db.String, nullable=False)
    score = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, nullable=False)
    current_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    quiz = db.relationship("Quiz")

class QuizAnswerLog(db.Model):
    __tablename__ = "quiz_answer_log"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("quiz_session.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("trivia_question.id"), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    client_ms = db.Column(db.Integer, default=0)
    awarded = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class LeaderboardEntry(db.Model):
    __tablename__ = "leaderboard_entry"
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    player_name = db.Column(db.String, nullable=False)
    score = db.Column(db.Integer, default=0)
    duration_ms = db.Column(db.Integer, nullable=True, default=0)  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
