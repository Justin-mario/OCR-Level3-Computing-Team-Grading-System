from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# Initialize Flask extensions
# db = SQLAlchemy()
# login_manager = LoginManager()
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__,
                template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
                static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'),
                instance_relative_config=True)

    # Load config
    app.config.from_object(Config)

    # Rest of your code remains the same
    ...
#
# def create_app():
#     app = Flask(__name__,
#                 template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
#                 static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'),
#                 instance_relative_config=True)

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Configuration
    app.config['SECRET_KEY'] = 'your-secret-key'  # Remove this
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(app.instance_path, "team_points.db")}'
    # app.config['SECRET_KEY'] = 'your-secret-key'
    # app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(app.instance_path, "team_points.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
                email='admin@example.com'  # Added email
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


