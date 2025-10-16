from flask import request, Blueprint, jsonify
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
from email_config import init_mail, send_verification_email, send_notification_email, generate_verification_token


auth_bp = Blueprint('auth', __name__)

# Rutas de autenticación
@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validar datos requeridos
    required_fields = ['email', 'password', 'first_name', 'last_name', 'role']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'message': f'El campo {field} es requerido'}), 400
    
    # Verificar si el usuario ya existe
    existing = query_one("SELECT id FROM users WHERE email=%s", (data['email'],))
    if existing:
        return jsonify({'message': 'El usuario ya existe'}), 400

    # Hash de contraseña con bcrypt (compatible con datos sembrados)
    pw_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Generar token de verificación
    verification_token = generate_verification_token()
    verification_expires = datetime.now() + timedelta(hours=24)

    try:
        user_id, _ = execute(
            """
            INSERT INTO users (email, password_hash, first_name, last_name, role, 
                             email_verified, verification_token, verification_token_expires)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                data['email'],
                pw_hash,
                data['first_name'],
                data['last_name'],
                data['role'],
                False,  # email_verified
                verification_token,
                verification_expires
            )
        )

        # Enviar email de verificación
        email_sent = send_verification_email(
            data['email'], 
            f"{data['first_name']} {data['last_name']}", 
            verification_token
        )
        
        if not email_sent:
            print(f"Advertencia: No se pudo enviar email de verificación a {data['email']}")

        access_token = create_access_token(identity=str(user_id))
        return jsonify({
            'message': 'Usuario creado exitosamente. Revisa tu email para verificar tu cuenta.',
            'access_token': access_token,
            'user': {
                'id': user_id,
                'email': data['email'],
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'role': data['role'],
                'email_verified': False
            },
            'email_verification_sent': email_sent
        }), 201
    except Exception as e:
        print(f"Error en registro: {e}")
        return jsonify({'message': 'Error al crear usuario'}), 500

@auth_bp.route('/api/auth/verify-email', methods=['POST'])
def verify_email():
    """Verifica el email del usuario usando el token"""
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify({'message': 'Token de verificación requerido'}), 400
    
    try:
        # Buscar usuario por token
        user = query_one("""
            SELECT id, email, first_name, last_name, verification_token_expires 
            FROM users 
            WHERE verification_token = %s AND email_verified = FALSE
        """, (token,))
        
        if not user:
            return jsonify({'message': 'Token de verificación inválido o ya usado'}), 400
        
        # Verificar si el token no ha expirado
        if datetime.now() > user['verification_token_expires']:
            return jsonify({'message': 'El token de verificación ha expirado'}), 400
        
        # Marcar email como verificado
        execute("""
            UPDATE users 
            SET email_verified = TRUE, verification_token = NULL, verification_token_expires = NULL 
            WHERE id = %s
        """, (user['id'],))
        
        return jsonify({
            'message': 'Email verificado exitosamente',
            'user': {
                'id': user['id'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'email_verified': True
            }
        }), 200
        
    except Exception as e:
        print(f"Error en verificación de email: {e}")
        return jsonify({'message': 'Error al verificar email'}), 500

@auth_bp.route('/api/auth/resend-verification', methods=['POST'])
@jwt_required()
def resend_verification():
    """Reenvía el email de verificación"""
    try:
        user_id = int(get_jwt_identity())
        user = query_one("""
            SELECT id, email, first_name, last_name, email_verified 
            FROM users WHERE id = %s
        """, (user_id,))
        
        if not user:
            return jsonify({'message': 'Usuario no encontrado'}), 404
        
        if user['email_verified']:
            return jsonify({'message': 'El email ya está verificado'}), 400
        
        # Generar nuevo token
        verification_token = generate_verification_token()
        verification_expires = datetime.now() + timedelta(hours=24)
        
        # Actualizar token en la base de datos
        execute("""
            UPDATE users 
            SET verification_token = %s, verification_token_expires = %s 
            WHERE id = %s
        """, (verification_token, verification_expires, user_id))
        
        # Enviar email
        email_sent = send_verification_email(
            user['email'], 
            f"{user['first_name']} {user['last_name']}", 
            verification_token
        )
        
        if email_sent:
            return jsonify({'message': 'Email de verificación reenviado'}), 200
        else:
            return jsonify({'message': 'Error al enviar email de verificación'}), 500
            
    except Exception as e:
        print(f"Error reenviando verificación: {e}")
        return jsonify({'message': 'Error al reenviar verificación'}), 500

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Email y contraseña son requeridos'}), 400
    
    user = query_one(
        "SELECT id, email, password_hash, first_name, last_name, role FROM users WHERE email=%s",
        (data['email'],)
    )

    if user and user.get('password_hash'):
        try:
            if bcrypt.checkpw(data['password'].encode('utf-8'), user['password_hash'].encode('utf-8')):
                access_token = create_access_token(identity=str(user['id']))
                return jsonify({
                    'access_token': access_token,
                    'user': {
                        'id': user['id'],
                        'email': user['email'],
                        'first_name': user['first_name'],
                        'last_name': user['last_name'],
                        'role': user['role']
                    }
                })
        except Exception:
            pass
    return jsonify({'message': 'Credenciales inválidas'}), 401

@auth_bp.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    user = query_one(
        "SELECT id, email, first_name, last_name, role, created_at FROM users WHERE id=%s",
        (current_user_id,)
    )

    if not user:
        return jsonify({'message': 'Usuario no encontrado'}), 404
    
    return jsonify({
        'id': user['id'],
        'email': user['email'],
        'first_name': user['first_name'],
        'last_name': user['last_name'],
        'role': user['role'],
        'created_at': user['created_at'].isoformat() if user['created_at'] else None
    })