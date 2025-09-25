from utils.db import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

class TriviaQuestion(db.Model):  # נשאיר את השם במחלקה, אבל נציג אותה כ-Library החוצה
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), unique=True, nullable=False)
    answer = db.Column(db.String(255), nullable=False)
    topic = db.Column(db.String(80), nullable=True)  # NEW: subject/topic instead of difficulty
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    #quiz_number = db.Column(db.int(80), nullable=False)

class QuizSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_name = db.Column(db.String(80), nullable=False)
    question_ids_csv = db.Column(db.String(255), nullable=False)
    current_index = db.Column(db.Integer, default=0, nullable=False)
    score = db.Column(db.Integer, default=0, nullable=False)
    is_finished = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

class LeaderboardEntry(db.Model):  # NEW
    id = db.Column(db.Integer, primary_key=True)
    player_name = db.Column(db.String(80), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    topic = db.Column(db.String(120), nullable=True)
    question_ids_csv = db.Column(db.Text, nullable=True)
