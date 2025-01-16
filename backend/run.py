from flask import Flask, request
from flask_cors import CORS
from auth import auth_bp, jwt, bcrypt
from dashboard import dashboard_bp
from models import db
import os

def create_app():
    flask_app = Flask(__name__)
    
    # Configure CORS with more permissive settings for development
    CORS(flask_app, 
         resources={
             r"/*": {
                 "origins": ["http://localhost:3000"],
                 "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                 "allow_headers": ["Content-Type", "Authorization", "Accept"],
                 "expose_headers": ["Content-Type", "Authorization"],
                 "supports_credentials": True
             }
         })
    
    # Configure database
    db_path = os.environ.get('DATABASE_URL', 'sqlite:///coffee_shop.db')
    if db_path.startswith('postgres://'):
        db_path = db_path.replace('postgres://', 'postgresql://', 1)
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = db_path
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configure JWT
    flask_app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
    flask_app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600  # 1 hour
    flask_app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 2592000  # 30 days
    flask_app.config['JWT_TOKEN_LOCATION'] = ['headers']
    flask_app.config['JWT_HEADER_NAME'] = 'Authorization'
    flask_app.config['JWT_HEADER_TYPE'] = 'Bearer'
    
    # Initialize extensions
    db.init_app(flask_app)
    jwt.init_app(flask_app)
    bcrypt.init_app(flask_app)
    
    # Register blueprints
    flask_app.register_blueprint(auth_bp, url_prefix='/auth')
    flask_app.register_blueprint(dashboard_bp, url_prefix='/api')
    
    return flask_app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5001, debug=True)
