from flask import Blueprint, request, jsonify
from sqlalchemy import func
from utils.db import db
from models import TriviaQuestion


play_bp = Blueprint("play_bp", __name__)

