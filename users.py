from flask import Blueprint, request, jsonify
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

from utils.db import db, Users
from utils.utils import users
from sqlalchemy import create_engine
current_id = 1

user_bp = Blueprint('user_bp', __name__)

# engine = create_engine(f"sqlite:///{db_path}", echo=True)
# db_connect = sessionmaker(bind=engine)
# db_session = db_connect()

@user_bp.get('/')
def show_users():
    return users
    # users = db_session.query(Users).all()
    # return jsonify([u.to_dict() for u in users])

@user_bp.post('/signup')
def signup():
    global current_id
    try:
        data = request.json
        if 'password' not in request.json.keys() or 'username' not in request.json.keys():
            return 'name and password are required ', 403
        data['password'] = generate_password_hash(data['password'])
        print(data)
        for user in users:
            if user['username'] == data['username']:
                return 'user already exists', 403

        users.append(data)
        # user1 = Users(username=data['username'], password=data['password'])
        # db.session.add(user1)
        # db.session.commit()
        return 'user added', 201

    except Exception as e:
        return str(e), 200


@user_bp.post('/login')
def login():
    username = request.json['username']
    password = request.json['password']

    user_data = get_user(username)
    if not user_data or not check_password_hash(user_data['password'], password):
        return "username or password incorrect", 401
    return "Login successful"


def get_user(username):
    return [u for u in users if u['username'] == username][0]