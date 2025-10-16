from flask import Flask, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import uuid
import mimetypes
from functools import wraps
from config import Config
from db import query_one, query_all, execute
import bcrypt
from routes.roles import role_required
from routes.files import allowed_file

from models import (
    db as models_db,
    Notification,
)


# Inicializar la instancia de models.db con la app y usarla localmente como db

app = Flask(__name__)
app.config.from_object(Config)
socketio = SocketIO(app, cors_allowed_origins=app.config['CORS_ORIGINS'])


db = models_db
models_db.init_app(app)

def create_notification(user_id, title, message, notification_type, related_id=None):
    """Crear una nueva notificación"""
    try:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            related_id=related_id
        )
        db.session.add(notification)
        db.session.commit()
        
        # Emitir notificación en tiempo real
        socketio.emit('new_notification', {
            'id': notification.id,
            'title': title,
            'message': message,
            'type': notification_type,
            'related_id': related_id,
            'created_at': notification.created_at.isoformat()
        }, room=f'user_{user_id}')
        
        return notification
    except Exception as e:
        db.session.rollback()
        print(f"Error creando notificación: {e}")
        return None
