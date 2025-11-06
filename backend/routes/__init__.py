# backend/routes/__init__.py
from .auth import auth_bp
from .users import users_bp
from .courses import courses_bp
from .assignments import assignments_bp
from .files import files_bp
from .notifications import notifications_bp

__all__ = ['auth_bp', 'users_bp', 'courses_bp', 'assignments_bp', 'notifications_bp','files_bp']
