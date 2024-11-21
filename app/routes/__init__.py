from .auth_routes import auth_bp
from .admin_routes import admin_bp
from .team_routes import team_bp

# This allows importing all blueprints from the routes package
__all__ = ['auth_bp', 'admin_bp', 'team_bp']