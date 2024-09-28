from flask import request, make_response, jsonify
from flask_restful import Resource
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from sqlalchemy.exc import IntegrityError
from app.models import db, User
from app.routes import auth_api

class SignUp(Resource):
    def post(self):
        data = request.get_json()
        try:
            new_user = User(
                username=data['username'],
                email=data['email'].lower()
            )
            new_user.set_password(data['password'])
            db.session.add(new_user)
            db.session.commit()
            
            # Generate tokens
            access_token = create_access_token(identity=new_user.id, additional_claims={"role": new_user.role})
            refresh_token = create_refresh_token(identity=new_user.id, additional_claims={"role": new_user.role})
            
            return make_response(jsonify({
                "message": "User created successfully",
                "access_token": access_token,
                "refresh_token": refresh_token
            }), 201)
        except IntegrityError:
            db.session.rollback()
            return make_response(jsonify({"message": "Username or email already exists"}), 400)
        except AssertionError as e:
            return make_response(jsonify({"message": str(e)}), 400)

class SignIn(Resource):
    def post(self):
        data = request.get_json()
        identifier = data.get('username') or data.get('email').lower()
        if not identifier or 'password' not in data:
            return make_response(jsonify({"message": "Missing username/email or password"}), 400)
        
        user = User.query.filter((User.email == identifier) | (User.username == identifier)).first()
        if not user:
            if 'username' in data:
                return make_response(jsonify({"message": "Invalid username"}), 401)
            else:
                return make_response(jsonify({"message": "Invalid email"}), 401)
        
        if not user.check_password(data['password']):
            return make_response(jsonify({"message": "Invalid password"}), 401)
        
        access_token = create_access_token(identity=user.id, additional_claims={"role": user.role})
        refresh_token = create_refresh_token(identity=user.id, additional_claims={"role": user.role})
        return make_response(jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token
        }), 200)

class RefreshToken(Resource):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        user = User.query.get(current_user)
        new_access_token = create_access_token(identity=current_user, additional_claims={"role": user.role})
        return make_response(jsonify({"access_token": new_access_token}), 200)

auth_api.add_resource(SignUp, '/signup')
auth_api.add_resource(SignIn, '/signin')
auth_api.add_resource(RefreshToken, '/refresh')