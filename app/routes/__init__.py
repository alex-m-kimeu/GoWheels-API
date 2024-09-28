from flask import Blueprint
from flask_restful import Api

auth_bp = Blueprint('auth', __name__)
user_bp = Blueprint('user', __name__)

auth_api = Api(auth_bp)
user_api = Api(user_bp)

from . import auth, user