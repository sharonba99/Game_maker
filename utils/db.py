
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)

class Topic(db.Model):
    __tablename__ = "topics"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Question(db.Model):
    __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    choice_a = db.Column(db.String(200), nullable=False)
    choice_b = db.Column(db.String(200), nullable=False)
    choice_c = db.Column(db.String(200), nullable=False)
    choice_d = db.Column(db.String(200), nullable=False)
    correct = db.Column(db.String(1), nullable=False)  # 'A'/'B'/'C'/'D'
    difficulty = db.Column(db.String(10), nullable=False, default="Easy")  # Easy/Medium/Hard
    topic = db.relationship("Topic", backref="questions")

class Game(db.Model):
    __tablename__ = "games"
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    current_index = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    topic = db.relationship("Topic")
    order_json = db.Column(db.Text, nullable=False)  # ordered question IDs (JSON)
    difficulty = db.Column(db.String(10), nullable=False, default="Any")  # stored for reference

class Player(db.Model):
    __tablename__ = "players"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    score = db.Column(db.Integer, default=0)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User")
    game = db.relationship("Game", backref="players")

class Answer(db.Model):
    __tablename__ = "answers"
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    selected = db.Column(db.String(1), nullable=False)  # 'A'/'B'/'C'/'D'
    is_correct = db.Column(db.Boolean, default=False)
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)
    player = db.relationship("Player")
    question = db.relationship("Question")

def seed_data():
    # Seed users
    for name in ["Roni", "Tomer", "Dani", "Mor"]:
        if not User.query.filter_by(username=name).first():
            db.session.add(User(username=name))

    def add_topic_with_questions(name, qs):
        topic = Topic.query.filter_by(name=name).first()
        if not topic:
            topic = Topic(name=name)
            db.session.add(topic)
            db.session.flush()
        if Question.query.filter_by(topic_id=topic.id).count() == 0:
            for q in qs:
                db.session.add(Question(
                    topic_id=topic.id,
                    text=q["text"],
                    choice_a=q["A"], choice_b=q["B"],
                    choice_c=q["C"], choice_d=q["D"],
                    correct=q["correct"],
                    difficulty=q["difficulty"]
                ))

    # MUSIC (12 Qs: 4 per difficulty)
    add_topic_with_questions("Music", [
        # Easy
        {"text":"Who is known as the 'King of Pop'?", "A":"Elvis Presley","B":"Michael Jackson","C":"Prince","D":"Stevie Wonder","correct":"B","difficulty":"Easy"},
        {"text":"Which band sang 'Hey Jude'?", "A":"The Rolling Stones","B":"The Beatles","C":"Queen","D":"ABBA","correct":"B","difficulty":"Easy"},
        {"text":"Which instrument has black and white keys?", "A":"Guitar","B":"Violin","C":"Piano","D":"Drums","correct":"C","difficulty":"Easy"},
        {"text":"Which singer released 'Shake It Off'?", "A":"Ariana Grande","B":"Taylor Swift","C":"Katy Perry","D":"Billie Eilish","correct":"B","difficulty":"Easy"},
        # Medium
        {"text":"Adele's debut album is titled…", "A":"17","B":"18","C":"19","D":"21","correct":"C","difficulty":"Medium"},
        {"text":"'Bohemian Rhapsody' was released by which band?", "A":"Queen","B":"Pink Floyd","C":"Led Zeppelin","D":"The Who","correct":"A","difficulty":"Medium"},
        {"text":"'Smells Like Teen Spirit' belongs to which band?", "A":"Pearl Jam","B":"Nirvana","C":"Foo Fighters","D":"Green Day","correct":"B","difficulty":"Medium"},
        {"text":"Which rapper released the album 'The Marshall Mathers LP'?", "A":"Kanye West","B":"Eminem","C":"Jay-Z","D":"Dr. Dre","correct":"B","difficulty":"Medium"},
        # Hard
        {"text":"Who composed 'The Four Seasons'?", "A":"Johann Sebastian Bach","B":"Antonio Vivaldi","C":"Ludwig van Beethoven","D":"Franz Schubert","correct":"B","difficulty":"Hard"},
        {"text":"Which producer pioneered the 'Wall of Sound' technique?", "A":"Phil Spector","B":"Brian Eno","C":"Quincy Jones","D":"George Martin","correct":"A","difficulty":"Hard"},
        {"text":"'Kind of Blue' is a landmark album by which jazz musician?", "A":"John Coltrane","B":"Miles Davis","C":"Charles Mingus","D":"Duke Ellington","correct":"B","difficulty":"Hard"},
        {"text":"Which singer used the stage name 'Ziggy Stardust'?", "A":"David Bowie","B":"Iggy Pop","C":"Lou Reed","D":"Morrissey","correct":"A","difficulty":"Hard"},
    ])

    # TELEVISION (12 Qs)
    add_topic_with_questions("Television", [
        # Easy
        {"text":"'Friends' is primarily set in which city?", "A":"Chicago","B":"New York","C":"Los Angeles","D":"Boston","correct":"B","difficulty":"Easy"},
        {"text":"Which show features a yellow family living in Springfield?", "A":"Family Guy","B":"The Simpsons","C":"South Park","D":"Bob's Burgers","correct":"B","difficulty":"Easy"},
        {"text":"Which series follows a group of survivors of a plane crash on a mysterious island?", "A":"Lost","B":"The 100","C":"Manifest","D":"The Leftovers","correct":"A","difficulty":"Easy"},
        {"text":"Which talk show host is famous for 'Carpool Karaoke'?", "A":"Jimmy Fallon","B":"James Corden","C":"Jimmy Kimmel","D":"Stephen Colbert","correct":"B","difficulty":"Easy"},
        # Medium
        {"text":"Walter White is the main character of which series?", "A":"Better Call Saul","B":"The Sopranos","C":"Breaking Bad","D":"Ozark","correct":"C","difficulty":"Medium"},
        {"text":"'Winter is Coming' is a motto from which show?", "A":"Vikings","B":"The Witcher","C":"Game of Thrones","D":"The Last Kingdom","correct":"C","difficulty":"Medium"},
        {"text":"Which series set in the 1980s features a group of kids in Hawkins, Indiana?", "A":"Dark","B":"Stranger Things","C":"Chernobyl","D":"Glow","correct":"B","difficulty":"Medium"},
        {"text":"'Dunder Mifflin' is the fictional paper company in…", "A":"Parks and Recreation","B":"Brooklyn Nine-Nine","C":"The Office (US)","D":"Silicon Valley","correct":"C","difficulty":"Medium"},
        # Hard
        {"text":"What is the name of the island in 'Lost' revealed by the DHARMA Initiative maps?", "A":"Hydra","B":"Craphole","C":"No official name","D":"Utopia","correct":"C","difficulty":"Hard"},
        {"text":"'Twin Peaks' was co-created by David Lynch and…", "A":"Mark Frost","B":"Chris Carter","C":"J.J. Abrams","D":"Damon Lindelof","correct":"A","difficulty":"Hard"},
        {"text":"'Black Mirror' first aired on which network?", "A":"Netflix","B":"Channel 4","C":"BBC Two","D":"ITV","correct":"B","difficulty":"Hard"},
        {"text":"Which series holds the record for most Emmy wins for a scripted series?", "A":"Game of Thrones","B":"Frasier","C":"Saturday Night Live","D":"The Crown","correct":"A","difficulty":"Hard"},
    ])

    # EUROVISION (12 Qs)
    add_topic_with_questions("Eurovision", [
        # Easy
        {"text":"Who won Eurovision 2018 with 'Toy'?", "A":"Netta (Israel)","B":"Eleni Foureira (Cyprus)","C":"Måneskin (Italy)","D":"Loreen (Sweden)","correct":"A","difficulty":"Easy"},
        {"text":"Which country hosted Eurovision 2022?", "A":"France","B":"Italy","C":"The Netherlands","D":"United Kingdom","correct":"B","difficulty":"Easy"},
        {"text":"Which contest is often abbreviated as ESC?", "A":"European Song Contest","B":"Eurovision Song Contest","C":"Euro Song Competition","D":"European Sound Championship","correct":"B","difficulty":"Easy"},
        {"text":"Which country is famous for ABBA's 1974 win?", "A":"Norway","B":"Finland","C":"Sweden","D":"Denmark","correct":"C","difficulty":"Easy"},
        # Medium
        {"text":"Which country has won Eurovision the most times?", "A":"Ireland","B":"Sweden","C":"United Kingdom","D":"France","correct":"B","difficulty":"Medium"},
        {"text":"Måneskin won Eurovision 2021 representing…", "A":"Spain","B":"Italy","C":"Portugal","D":"Germany","correct":"B","difficulty":"Medium"},
        {"text":"'Euphoria' won Eurovision 2012 for which artist?", "A":"Conchita Wurst","B":"Loreen","C":"Alexander Rybak","D":"Duncan Laurence","correct":"B","difficulty":"Medium"},
        {"text":"Which city hosted Eurovision 2019?", "A":"Lisbon","B":"Tel Aviv","C":"Rotterdam","D":"Turin","correct":"B","difficulty":"Medium"},
        # Hard
        {"text":"Ireland achieved a rare three-peat of wins in which years?", "A":"1992–1994","B":"1993–1995","C":"1994–1996","D":"1991–1993","correct":"A","difficulty":"Hard"},
        {"text":"Which artist holds the record for the highest televote points under the current system (as of 2023)?", "A":"Loreen","B":"Salvador Sobral","C":"Kalush Orchestra","D":"Chanel","correct":"C","difficulty":"Hard"},
        {"text":"Which non-winning song became a global hit in 2022 from Spain?", "A":"Brividi","B":"SloMo","C":"Stefania","D":"Snap","correct":"B","difficulty":"Hard"},
        {"text":"Which year introduced the semi-final format?", "A":"2000","B":"2004","C":"2008","D":"2010","correct":"B","difficulty":"Hard"},
    ])

    db.session.commit()
