from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.orm import validates
from sqlalchemy.sql import func
import re
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pytz

db = SQLAlchemy()

# User Model
class User(db.Model, SerializerMixin):
    __tablename__ = 'users'
    
    # columns
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(), unique=True, nullable=False)
    email = db.Column(db.String(), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
    image = db.Column(db.String(), nullable=True)
    role = db.Column(db.String(), nullable=False, default="customer")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(pytz.utc))
    updated_at = db.Column(db.DateTime, nullable=True, default=lambda: datetime.now(pytz.utc), onupdate=lambda: datetime.now(pytz.utc))

    # validations
    @validates('username')
    def validate_username(self, key, username):
        assert username, "Username should not be empty"
        assert len(username) >= 3, "Username should be at least 3 characters long"
        assert re.match(r"^[a-zA-Z0-9_]+$", username), "Username should contain only letters, numbers, and underscores"
        
        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        assert existing_user is None, "Username already exists"
        
        return username

    @validates('email')
    def validate_email(self, key, email):
        assert email, "Email should not be empty"
        assert '@' in email, 'Invalid email format'
        assert re.match(r"[^@]+@[^@]+\.[^@]+", email), 'Invalid email format'
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        assert existing_user is None, "Email already exists"
        
        return email

    def set_password(self, password):
        assert password, "Password should not be empty"
        assert len(password) >= 6, "Password should be at least 6 characters long"
        assert re.search(r"[A-Z]", password), "Password should contain at least one uppercase letter"
        assert re.search(r"[a-z]", password), "Password should contain at least one lowercase letter"
        assert re.search(r"[0-9]", password), "Password should contain at least one digit"
        assert re.search(r"[!@#$%^&*(),.?\":{}|<>]", password), "Password should contain at least one special character"
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @validates('image')
    def validate_image(self, key, image):
        if image:
            assert re.match(r"^https?://", image), "Image URL should be valid"
        return image
    
    @validates('role')
    def validate_role(self, key, role):
        assert role in ["customer", "admin"], "Role should be either 'customer' or 'admin'"
        return role
    
    # Function to upload an image to Cloudinary
    def upload_image(self, image):
        try:
            upload_result = cloudinary.uploader.upload(image)
            optimized_url, _ = cloudinary_url(
                upload_result['public_id'],
                fetch_format="auto",
                quality="auto"
            )
            # Use the optimized URL
            self.image = optimized_url
        except Exception as e:
            raise ValueError(f"Image upload failed: {e}")