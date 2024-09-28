from flask import Flask
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import cloudinary
from .config import Config
from .models import db
from .routes import auth_bp, user_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    cloudinary.config( 
        cloud_name=Config.CLOUDINARY_CLOUD_NAME, 
        api_key=Config.CLOUDINARY_API_KEY, 
        api_secret=Config.CLOUDINARY_API_SECRET, 
        secure=True
    )

    migrate = Migrate(app, db)
    db.init_app(app)
    bcrypt = Bcrypt(app)
    jwt = JWTManager(app)
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/api')

    return app