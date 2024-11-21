import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Basic Flask config
    SECRET_KEY = os.getenv('SECRET_KEY') or 'your-secret-key-here'

    # Database config
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or 'sqlite:///team_points.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Admin account
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME') or 'admin'
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD') or 'password'
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL') or 'admin@example.com'