import os
from datetime import timedelta

class Config:
    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///coffee_shop.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration
    JWT_SECRET_KEY = 'dev-secret-key'  # Change in production
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Flask Configuration
    SECRET_KEY = 'dev-secret-key'  # Change in production
    
    # CORS Configuration
    CORS_HEADERS = 'Content-Type'
