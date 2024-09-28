from flask import request, make_response, jsonify
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy.exc import IntegrityError
from app.models import db, User
from app.routes import user_api

# Decorator to check roles
def role_required(role):
    def decorator(fn):
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims['role'] != role:
                return make_response(jsonify({"message": "Access forbidden: insufficient permissions"}), 403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator

class Users(Resource):
    @jwt_required()
    def get(self):
        users = User.query.all()
        return make_response(jsonify([user.to_dict() for user in users]), 200)

    @jwt_required()
    def post(self):
        data = request.get_json()
        claims = get_jwt()
        
        # Check if the current user is trying to assign the admin role
        if data.get('role') == 'admin' and claims['role'] != 'admin':
            return make_response(jsonify({"message": "Only admins can assign the admin role"}), 403)
        
        try:
            new_user = User(
                username=data['username'],
                email=data['email'].lower(),
                role=data.get('role', 'customer')
            )
            new_user.set_password(data['password'])
            db.session.add(new_user)
            db.session.commit()
            return make_response(jsonify({"message": "User created successfully"}), 201)
        except IntegrityError:
            db.session.rollback()
            return make_response(jsonify({"message": "Username or email already exists"}), 400)
        except AssertionError as e:
            return make_response(jsonify({"message": str(e)}), 400)

class UserByID(Resource):
    @jwt_required()
    def get(self, user_id):
        user = User.query.get_or_404(user_id)
        return make_response(jsonify(user.to_dict()), 200)

    @jwt_required()
    def patch(self):
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        data = request.form
        image = request.files.get('image')
        
        try:
            if 'username' in data:
                user.username = data['username']
            if 'email' in data:
                user.email = data['email'].lower()
            if 'password' in data:
                user.set_password(data['password'])
            if image:
                user.upload_image(image)
            db.session.commit()
            return make_response(jsonify({"message": "User updated successfully"}), 200)
        except IntegrityError:
            db.session.rollback()
            return make_response(jsonify({"message": "Username or email already exists"}), 400)
        except AssertionError as e:
            return make_response(jsonify({"message": str(e)}), 400)

    @jwt_required()
    @role_required('admin')
    def delete(self, user_id):
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return make_response(jsonify({"message": "User deleted successfully"}), 200)

user_api.add_resource(Users, '/users')
user_api.add_resource(UserByID, '/users/<int:user_id>')
user_api.add_resource(UserByID, '/users/me', endpoint='user_me')