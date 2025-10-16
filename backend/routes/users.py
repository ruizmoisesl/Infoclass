from flask import Flask,request, Blueprint, jsonify
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

users_bp = Blueprint('users', __name__)

app = Flask(__name__)
app.config.from_object(Config)

from models import (db as models_db,User)

# Inicializar la instancia de models.db con la app y usarla localmente como db
models_db.init_app(app)
db = models_db


# Rutas de gestión de usuarios
@users_bp.route('/api/users', methods=['GET'])
@jwt_required()
@role_required(['admin'])
def get_users():
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': user.role,
        'is_active': user.is_active,
        'created_at': user.created_at.isoformat()
    } for user in users])

@users_bp.route('/api/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@role_required(['admin'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if 'is_active' in data:
        user.is_active = data['is_active']
    
    if 'role' in data:
        user.role = data['role']
    
    try:
        db.session.commit()
        return jsonify({'message': 'Usuario actualizado exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al actualizar usuario'}), 500

# Endpoints para perfil de usuario
@users_bp.route('/api/users/stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    """Obtiene estadísticas del usuario actual"""
    try:
        user_id = int(get_jwt_identity())
        
        # Obtener estadísticas del usuario
        stats = query_one("""
            SELECT 
                (SELECT COUNT(*) FROM course_enrollments WHERE student_id = %s) as courses,
                (SELECT COUNT(*) FROM assignment_submissions WHERE student_id = %s) as submissions,
                (SELECT AVG(points_earned) FROM assignment_submissions WHERE student_id = %s AND points_earned IS NOT NULL) as average_grade
        """, (user_id, user_id, user_id))
        
        # Obtener número de tareas asignadas
        assignments_count = query_one("""
            SELECT COUNT(*) as count
            FROM assignments a
            JOIN course_enrollments ce ON a.course_id = ce.course_id
            WHERE ce.student_id = %s
        """, (user_id,))
        
        return jsonify({
            'courses': stats['courses'] or 0,
            'assignments': assignments_count['count'] or 0,
            'submissions': stats['submissions'] or 0,
            'average': round(float(stats['average_grade'] or 0), 2)
        })
        
    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")
        return jsonify({'message': 'Error al obtener estadísticas'}), 500

@users_bp.route('/api/users/notification-settings', methods=['GET'])
@jwt_required()
def get_notification_settings():
    """Obtiene la configuración de notificaciones del usuario"""
    try:
        user_id = int(get_jwt_identity())
        
        settings = query_one("""
            SELECT email_notifications, assignment_reminders, grade_notifications, announcement_notifications
            FROM users WHERE id = %s
        """, (user_id,))
        
        if not settings:
            return jsonify({'message': 'Usuario no encontrado'}), 404
        
        return jsonify({
            'email_notifications': bool(settings['email_notifications']),
            'assignment_reminders': bool(settings['assignment_reminders']),
            'grade_notifications': bool(settings['grade_notifications']),
            'announcement_notifications': bool(settings['announcement_notifications'])
        })
        
    except Exception as e:
        print(f"Error obteniendo configuración de notificaciones: {e}")
        return jsonify({'message': 'Error al obtener configuración'}), 500

@users_bp.route('/api/users/notification-settings', methods=['PUT'])
@jwt_required()
def update_notification_settings():
    """Actualiza la configuración de notificaciones del usuario"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        # Validar datos
        valid_fields = ['email_notifications', 'assignment_reminders', 'grade_notifications', 'announcement_notifications']
        update_fields = []
        update_values = []
        
        for field in valid_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                update_values.append(bool(data[field]))
        
        if not update_fields:
            return jsonify({'message': 'No hay campos para actualizar'}), 400
        
        update_values.append(user_id)
        
        execute(f"""
            UPDATE users 
            SET {', '.join(update_fields)}
            WHERE id = %s
        """, tuple(update_values))
        
        return jsonify({'message': 'Configuración actualizada exitosamente'})
        
    except Exception as e:
        print(f"Error actualizando configuración: {e}")
        return jsonify({'message': 'Error al actualizar configuración'}), 500

@users_bp.route('/api/users/profile', methods=['PUT'])
@jwt_required()
def update_user_profile():
    """Actualiza el perfil del usuario"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        # Validar datos
        valid_fields = ['first_name', 'last_name', 'bio', 'phone', 'website']
        update_fields = []
        update_values = []
        
        for field in valid_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                update_values.append(data[field])
        
        if not update_fields:
            return jsonify({'message': 'No hay campos para actualizar'}), 400
        
        update_values.append(user_id)
        
        execute(f"""
            UPDATE users 
            SET {', '.join(update_fields)}
            WHERE id = %s
        """, tuple(update_values))
        
        # Obtener usuario actualizado
        updated_user = query_one("""
            SELECT id, email, first_name, last_name, role, bio, phone, website, email_verified, created_at
            FROM users WHERE id = %s
        """, (user_id,))
        
        return jsonify({
            'message': 'Perfil actualizado exitosamente',
            'user': {
                'id': updated_user['id'],
                'email': updated_user['email'],
                'first_name': updated_user['first_name'],
                'last_name': updated_user['last_name'],
                'role': updated_user['role'],
                'bio': updated_user['bio'],
                'phone': updated_user['phone'],
                'website': updated_user['website'],
                'email_verified': bool(updated_user['email_verified']),
                'created_at': updated_user['created_at'].isoformat() if updated_user['created_at'] else None
            }
        })
        
    except Exception as e:
        print(f"Error actualizando perfil: {e}")
        return jsonify({'message': 'Error al actualizar perfil'}), 500

@users_bp.route('/api/users/password', methods=['PUT'])
@jwt_required()
def update_user_password():
    """Actualiza la contraseña del usuario"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'message': 'Contraseña actual y nueva contraseña son requeridas'}), 400
        
        if len(new_password) < 6:
            return jsonify({'message': 'La nueva contraseña debe tener al menos 6 caracteres'}), 400
        
        # Verificar contraseña actual
        user = query_one("SELECT password_hash FROM users WHERE id = %s", (user_id,))
        if not user:
            return jsonify({'message': 'Usuario no encontrado'}), 404
        
        if not bcrypt.checkpw(current_password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return jsonify({'message': 'Contraseña actual incorrecta'}), 400
        
        # Actualizar contraseña
        new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_password_hash, user_id))
        
        return jsonify({'message': 'Contraseña actualizada exitosamente'})
        
    except Exception as e:
        print(f"Error actualizando contraseña: {e}")
        return jsonify({'message': 'Error al actualizar contraseña'}), 500

@users_bp.route('/api/users/avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    """Sube un avatar para el usuario"""
    try:
        user_id = int(get_jwt_identity())
        
        if 'avatar' not in request.files:
            return jsonify({'message': 'No se encontró archivo de avatar'}), 400
        
        file = request.files['avatar']
        if file.filename == '':
            return jsonify({'message': 'No se seleccionó archivo'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'message': 'Tipo de archivo no permitido'}), 400
        
        # Generar nombre único para el archivo
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"avatar_{user_id}_{uuid.uuid4().hex}.{file_extension}"
        
        # Crear directorio de avatares si no existe
        avatar_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'avatars')
        os.makedirs(avatar_dir, exist_ok=True)
        
        # Guardar archivo
        file_path = os.path.join(avatar_dir, unique_filename)
        file.save(file_path)
        
        # Actualizar base de datos
        avatar_url = f"/uploads/avatars/{unique_filename}"
        execute("UPDATE users SET avatar = %s WHERE id = %s", (avatar_url, user_id))
        
        # Obtener usuario actualizado
        updated_user = query_one("""
            SELECT id, email, first_name, last_name, role, avatar, email_verified, created_at
            FROM users WHERE id = %s
        """, (user_id,))
        
        return jsonify({
            'message': 'Avatar actualizado exitosamente',
            'user': {
                'id': updated_user['id'],
                'email': updated_user['email'],
                'first_name': updated_user['first_name'],
                'last_name': updated_user['last_name'],
                'role': updated_user['role'],
                'avatar': updated_user['avatar'],
                'email_verified': bool(updated_user['email_verified']),
                'created_at': updated_user['created_at'].isoformat() if updated_user['created_at'] else None
            }
        })
        
    except Exception as e:
        print(f"Error subiendo avatar: {e}")
        return jsonify({'message': 'Error al subir avatar'}), 500

@users_bp.route('/api/users/avatar', methods=['DELETE'])
@jwt_required()
def delete_avatar():
    """Elimina el avatar del usuario"""
    try:
        user_id = int(get_jwt_identity())
        
        # Obtener avatar actual
        user = query_one("SELECT avatar FROM users WHERE id = %s", (user_id,))
        if not user:
            return jsonify({'message': 'Usuario no encontrado'}), 404
        
        # Eliminar archivo si existe
        if user['avatar']:
            avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], user['avatar'].replace('/uploads/', ''))
            if os.path.exists(avatar_path):
                os.remove(avatar_path)
        
        # Actualizar base de datos
        execute("UPDATE users SET avatar = NULL WHERE id = %s", (user_id,))
        
        # Obtener usuario actualizado
        updated_user = query_one("""
            SELECT id, email, first_name, last_name, role, avatar, email_verified, created_at
            FROM users WHERE id = %s
        """, (user_id,))
        
        return jsonify({
            'message': 'Avatar eliminado exitosamente',
            'user': {
                'id': updated_user['id'],
                'email': updated_user['email'],
                'first_name': updated_user['first_name'],
                'last_name': updated_user['last_name'],
                'role': updated_user['role'],
                'avatar': updated_user['avatar'],
                'email_verified': bool(updated_user['email_verified']),
                'created_at': updated_user['created_at'].isoformat() if updated_user['created_at'] else None
            }
        })
        
    except Exception as e:
        print(f"Error eliminando avatar: {e}")
        return jsonify({'message': 'Error al eliminar avatar'}), 500
