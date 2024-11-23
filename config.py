# import os
# from dotenv import load_dotenv
#
# load_dotenv()
#
#
# class Config:
#     # Basic Flask config
#     SECRET_KEY = os.getenv('SECRET_KEY') or 'your-secret-key-here'
#
#     # Database config
#     SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or 'sqlite:///team_points.db'
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#
#     # Admin account
#     ADMIN_USERNAME = os.getenv('ADMIN_USERNAME') or 'admin'
#     ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD') or 'password'
#     ADMIN_EMAIL = os.getenv('ADMIN_EMAIL') or 'admin@example.com'


# config.py
import os
from dotenv import load_dotenv

load_dotenv()


# class Config:
#     SECRET_KEY = os.getenv('SECRET_KEY')
#     SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
#     if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
#         SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///team_points.db')
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Remove hardcoded values
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')