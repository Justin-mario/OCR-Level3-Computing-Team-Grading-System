from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
import os
import sys

# Initialize Flask extensions
db = SQLAlchemy()
login_manager = LoginManager()

# Add parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_app():
    app = Flask(__name__,
                template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
                static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'),
                instance_relative_config=True)

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Load config
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Register blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.team_routes import team_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(team_bp)

    # Create database tables
    with app.app_context():
        db.create_all()

        # Create default admin user if it doesn't exist
        from app.models.entities import Admin
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(
                username='admin',
                email='admin@example.com'
            )
            admin.set_password('password')
            db.session.add(admin)
            db.session.commit()

    return app

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from app.models.entities import Admin
    return Admin.query.get(int(user_id))