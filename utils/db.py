from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(1100), unique=True, nullable=False)

    def __repr__(self):
        return f'User-{self.id} ({self.username}),'

    def to_dict(self):
        return {"id": self.id, "username": self.username, "password": self.password}