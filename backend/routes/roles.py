from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from db import query_one
from functools import wraps

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = query_one("SELECT id, role FROM users WHERE id=%s", (current_user_id,))
            if not user or user["role"] not in roles:
                return jsonify({'message': 'Acceso denegado'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
