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

# Create Main Admin User
def create_admin_user():
    admin_email = 'gowheels@admin.co.ke'
    admin_username = 'GoWheelsAdmin'
    admin_password = 'Admin@123'
    
    existing_admin = User.query.filter_by(email=admin_email).first()
    if not existing_admin:
        try:
            admin_user = User(
                username=admin_username,
                email=admin_email,
                role='admin'
            )
            admin_user.set_password(admin_password)
            db.session.add(admin_user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        except AssertionError as e:
            print(f"Failed to create admin user: {str(e)}")

class Users(Resource):
    @jwt_required()
    @role_required('admin')
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
    def get(self, user_id=None):
        if user_id is None:
            user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        return make_response(jsonify(user.to_dict()), 200)

    @jwt_required()
    def patch(self, user_id=None):
        if user_id is None:
            user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        data = request.form
        image = request.files.get('image')
        
        try:
            if 'username' in data:
                user.username = data['username']
            if 'email' in data:
                user.email = data['email'].lower()
            if 'old_password' in data and 'new_password' in data:
                if user.check_password(data['old_password']):
                    if data['old_password'] == data['new_password']:
                        return make_response(jsonify({"message": "New password cannot be the same as the old password"}), 400)
                    user.set_password(data['new_password'])
                else:
                    return make_response(jsonify({"message": "Old password is incorrect"}), 400)
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
user_api.add_resource(UserByID, '/user', '/user/<int:user_id>')