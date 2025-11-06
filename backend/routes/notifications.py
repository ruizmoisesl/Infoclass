from flask import Flask, jsonify, Blueprint
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
from utils import allowed_file

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

notifications_bp = Blueprint('notifications', __name__)

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


@notifications_bp.route('/api/notifications/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_notification_read(notification_id):
    current_user_id = int(get_jwt_identity())
    
    try:
        notification = Notification.query.filter_by(
            id=notification_id, 
            user_id=current_user_id
        ).first()
        
        if not notification:
            return jsonify({'message': 'Notificación no encontrada'}), 404
        
        notification.is_read = True
        db.session.commit()
        
        return jsonify({'message': 'Notificación marcada como leída'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al marcar notificación'}), 500

@notifications_bp.route('/api/notifications/read-all', methods=['PUT'])
@jwt_required()
def mark_all_notifications_read():
    current_user_id = int(get_jwt_identity())
    
    try:
        Notification.query.filter_by(user_id=current_user_id, is_read=False)\
            .update({'is_read': True})
        db.session.commit()
        
        return jsonify({'message': 'Todas las notificaciones marcadas como leídas'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al marcar notificaciones'}), 500


@notifications_bp.route('/api/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    current_user_id = int(get_jwt_identity())
    
    try:
        notifications = Notification.query.filter_by(user_id=current_user_id)\
            .order_by(Notification.created_at.desc())\
            .limit(50).all()
        
        return jsonify([{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.type,
            'is_read': n.is_read,
            'related_id': n.related_id,
            'created_at': n.created_at.isoformat()
        } for n in notifications])
        
    except Exception as e:
        return jsonify({'message': 'Error al obtener notificaciones'}), 500

