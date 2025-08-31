from flask import Blueprint, request
from werkzeug.security import generate_password_hash, check_password_hash
from utils.utils import users, points

current_id = 1


user_bp = Blueprint('user_bp', __name__)


@user_bp.get('/')
def show_users():
    return users

#get user by id
@user_bp.get('/<int:id>')
def show_by_id(id):
    for user in users:
        if user["id"] == id:
            return user
    return "No user found" , 404

#add user
@user_bp.post('/signup')
def signup():
    global current_id
    try:
        data = request.json
        data["id"] = current_id
        data["points"] = points
        if 'password' not in request.json.keys() or 'username' not in request.json.keys():
            return 'name and password are required ', 403
        data['password'] = generate_password_hash(data['password'])
        print(data)
        for user in users:
            if user['username'] == data['username']:
                return 'user already exists', 403

        users.append(data)
        current_id += 1
        # user1 = Users(username=data['username'], password=data['password'])
        # db.session.add(user1)
        # db.session.commit()
        return 'user added', 201

    except Exception as e:
        return str(e), 200

#login as user
@user_bp.post('/login')
def login():
    username = request.json['username']
    password = request.json['password']

    user_data = get_users(username)
    if not user_data or not check_password_hash(user_data['password'], password):
        return "username or password incorrect", 401
    return "Login successful", 200


def get_users(username):
    return [u for u in users if u['username'] == username][0]