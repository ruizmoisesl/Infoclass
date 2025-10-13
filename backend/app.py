from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
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

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar Flask-Mail
mail = init_mail(app)
app.mail = mail

# Configuración para archivos
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Crear directorio de uploads si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_mime_type_by_extension(extension):
    """Obtener tipo MIME por extensión de archivo"""
    mime_types = {
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'ppt': 'application/vnd.ms-powerpoint',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'txt': 'text/plain',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'svg': 'image/svg+xml',
        'zip': 'application/zip',
        'rar': 'application/x-rar-compressed',
        '7z': 'application/x-7z-compressed',
        'mp4': 'video/mp4',
        'avi': 'video/x-msvideo',
        'mov': 'video/quicktime',
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
        'csv': 'text/csv',
        'json': 'application/json',
        'xml': 'application/xml',
        'html': 'text/html',
        'css': 'text/css',
        'js': 'application/javascript',
        'py': 'text/x-python',
        'java': 'text/x-java-source',
        'cpp': 'text/x-c++src',
        'c': 'text/x-csrc',
        'h': 'text/x-chdr',
        'php': 'application/x-httpd-php',
        'sql': 'application/sql',
        'md': 'text/markdown',
        'rtf': 'application/rtf'
    }
    return mime_types.get(extension.lower(), 'application/octet-stream')

# Inicialización de extensiones (usar la instancia de models.db)
jwt = JWTManager(app)
CORS(app, origins=app.config['https://infoclass-theta.vercel.app'])
socketio = SocketIO(app, cors_allowed_origins=app.config['https://infoclass-theta.vercel.app'])

# Importar modelos y unificar la instancia de DB
from models import (
    db as models_db,
    User,
    Course,
    CourseEnrollment,
    Assignment,
    AssignmentSubmission,
    Announcement,
    Comment,
    Message,
    Notification,
    FileAttachment,
)

# Inicializar la instancia de models.db con la app y usarla localmente como db
models_db.init_app(app)
db = models_db

# Decorador para verificar roles
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

# Rutas de autenticación
@app.route('/api/auth/register', methods=['POST'])
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

@app.route('/api/auth/verify-email', methods=['POST'])
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

@app.route('/api/auth/resend-verification', methods=['POST'])
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

@app.route('/api/auth/login', methods=['POST'])
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

@app.route('/api/auth/me', methods=['GET'])
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

# Rutas de gestión de usuarios
@app.route('/api/users', methods=['GET'])
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

@app.route('/api/users/<int:user_id>', methods=['PUT'])
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
@app.route('/api/users/stats', methods=['GET'])
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

@app.route('/api/users/notification-settings', methods=['GET'])
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

@app.route('/api/users/notification-settings', methods=['PUT'])
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

@app.route('/api/users/profile', methods=['PUT'])
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

@app.route('/api/users/password', methods=['PUT'])
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

@app.route('/api/users/avatar', methods=['POST'])
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

@app.route('/api/users/avatar', methods=['DELETE'])
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

# Rutas de gestión de cursos
@app.route('/api/courses', methods=['GET'])
@jwt_required()
def get_courses():
    current_user_id = int(get_jwt_identity())
    # Resolver rol del usuario actual
    u = query_one("SELECT id, role FROM users WHERE id=%s", (current_user_id,))
    if not u:
        return jsonify({'message': 'Usuario no encontrado'}), 404

    role = u['role']
    rows = []
    if role == 'teacher':
        rows = query_all(
            """
            SELECT c.*, t.id AS teacher_id, t.first_name AS teacher_first_name, t.last_name AS teacher_last_name
            FROM courses c
            JOIN users t ON t.id = c.teacher_id
            WHERE c.teacher_id = %s
            ORDER BY c.created_at DESC
            """,
            (current_user_id,)
        )
    elif role == 'student':
        rows = query_all(
            """
            SELECT c.*, t.id AS teacher_id, t.first_name AS teacher_first_name, t.last_name AS teacher_last_name
            FROM course_enrollments ce
            JOIN courses c ON c.id = ce.course_id
            JOIN users t ON t.id = c.teacher_id
            WHERE ce.student_id = %s
            ORDER BY c.created_at DESC
            """,
            (current_user_id,)
        )
    else:  # admin
        rows = query_all(
            """
            SELECT c.*, t.id AS teacher_id, t.first_name AS teacher_first_name, t.last_name AS teacher_last_name
            FROM courses c
            JOIN users t ON t.id = c.teacher_id
            ORDER BY c.created_at DESC
            """
        )

    def map_course(r):
        return {
            'id': r['id'],
            'name': r['name'],
            'description': r.get('description'),
            'section': r.get('section'),
            'subject': r.get('subject'),
            'room': r.get('room'),
            'access_code': r.get('access_code'),
            'is_active': bool(r.get('is_active')) if r.get('is_active') is not None else True,
            'teacher': {
                'id': r['teacher_id'],
                'first_name': r['teacher_first_name'],
                'last_name': r['teacher_last_name']
            },
            'created_at': r['created_at'].isoformat() if r.get('created_at') else None
        }

    return jsonify([map_course(r) for r in rows])

@app.route('/api/courses', methods=['POST'])
@jwt_required()
@role_required(['teacher', 'admin'])
def create_course():
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    # Generar código de acceso único
    import random
    import string
    access_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    try:
        new_id, _ = execute(
            """
            INSERT INTO courses (name, description, section, subject, room, access_code, teacher_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                data['name'],
                data.get('description', ''),
                data.get('section', ''),
                data.get('subject', ''),
                data.get('room', ''),
                access_code,
                current_user_id,
            )
        )

        return jsonify({
            'message': 'Curso creado exitosamente',
            'course': {
                'id': new_id,
                'name': data['name'],
                'access_code': access_code
            }
        }), 201
    except Exception as e:
        return jsonify({'message': 'Error al crear curso'}), 500

@app.route('/api/courses/enroll', methods=['POST'])
@jwt_required()
@role_required(['student'])
def enroll_by_code():
    """Permite a un estudiante inscribirse a un curso usando solo el código de acceso."""
    current_user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    access_code = data.get('access_code')

    if not access_code:
        return jsonify({'message': 'El código de acceso es requerido'}), 400

    # Buscar curso por código usando SQL directo
    course_row = query_one(
        "SELECT id FROM courses WHERE access_code=%s",
        (access_code,)
    )

    if not course_row:
        return jsonify({'message': 'Código de acceso inválido'}), 400

    course_id = course_row['id']

    # Verificar si ya está inscrito
    existing = query_one(
        "SELECT id FROM course_enrollments WHERE student_id=%s AND course_id=%s",
        (current_user_id, course_id)
    )
    if existing:
        return jsonify({'message': 'Ya estás inscrito en este curso'}), 400

    try:
        execute(
            "INSERT INTO course_enrollments (student_id, course_id) VALUES (%s, %s)",
            (current_user_id, course_id)
        )
        return jsonify({'message': 'Inscripción exitosa', 'course_id': course_id}), 201
    except Exception as e:
        return jsonify({'message': 'Error al inscribirse'}), 500

@app.route('/api/courses/<int:course_id>/enroll', methods=['POST'])
@jwt_required()
@role_required(['student'])
def enroll_in_course(course_id):
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    course = Course.query.get_or_404(course_id)
    
    # Verificar código de acceso
    if course.access_code != data.get('access_code'):
        return jsonify({'message': 'Código de acceso inválido'}), 400
    
    # Verificar si ya está inscrito
    existing_enrollment = CourseEnrollment.query.filter_by(
        student_id=current_user_id,
        course_id=course_id
    ).first()
    
    if existing_enrollment:
        return jsonify({'message': 'Ya estás inscrito en este curso'}), 400
    
    enrollment = CourseEnrollment(
        student_id=current_user_id,
        course_id=course_id
    )
    
    try:
        db.session.add(enrollment)
        db.session.commit()
        
        return jsonify({'message': 'Inscripción exitosa'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al inscribirse'}), 500
# Rutas de gestión de tareas
@app.route('/api/assignments', methods=['GET'])
@jwt_required()
def get_all_assignments():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    include_archived = request.args.get('include_archived', 'false').lower() == 'true'

    assignments = []
    if user.role == 'teacher':
        # Profesores: tareas de sus cursos
        courses = Course.query.filter_by(teacher_id=current_user_id).all()
        course_ids = [c.id for c in courses]
        q = Assignment.query.filter(Assignment.course_id.in_(course_ids))
        if not include_archived:
            q = q.filter_by(is_archived=False)
        assignments = q.all()
    elif user.role == 'student':
        # Estudiantes: tareas de cursos donde están inscritos
        enrollments = CourseEnrollment.query.filter_by(student_id=current_user_id).all()
        course_ids = [e.course_id for e in enrollments]
        q = Assignment.query.filter(Assignment.course_id.in_(course_ids))
        if not include_archived:
            q = q.filter_by(is_archived=False)
        assignments = q.all()
        # Cargar estado de mi entrega para cada tarea
        assignment_ids = [a.id for a in assignments]
        submissions = AssignmentSubmission.query.with_entities(
            AssignmentSubmission.assignment_id,
            AssignmentSubmission.status,
            AssignmentSubmission.submitted_at
        ).filter(
            AssignmentSubmission.student_id == current_user_id,
            AssignmentSubmission.assignment_id.in_(assignment_ids)
        ).all()
        sub_map = {aid: {'status': status, 'submitted_at': (submitted_at.isoformat() if submitted_at else None)} for aid, status, submitted_at in submissions}
    else:  # admin
        q = Assignment.query
        if not include_archived:
            q = q.filter_by(is_archived=False)
        assignments = q.all()

    return jsonify([{
        'id': a.id,
        'title': a.title,
        'description': a.description,
        'due_date': a.due_date.isoformat(),
        'max_points': float(a.max_points),
        'allow_late_submissions': a.allow_late_submissions,
        'is_archived': a.is_archived,
        'course': {
            'id': a.course.id,
            'name': a.course.name
        },
        'created_at': a.created_at.isoformat() if a.created_at else None,
        # Incluir mi entrega solo si soy estudiante
        **({'submission': sub_map.get(a.id)} if user.role == 'student' else {})
    } for a in assignments])

@app.route('/api/courses/<int:course_id>/assignments', methods=['GET'])
@jwt_required()
def get_assignments(course_id):
    include_archived = request.args.get('include_archived', 'false').lower() == 'true'
    q = Assignment.query.filter_by(course_id=course_id)
    if not include_archived:
        q = q.filter_by(is_archived=False)
    assignments = q.all()
    # Si es estudiante, adjuntar su estado de entrega
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    sub_map = {}
    if user and user.role == 'student' and assignments:
        assignment_ids = [a.id for a in assignments]
        submissions = AssignmentSubmission.query.with_entities(
            AssignmentSubmission.assignment_id,
            AssignmentSubmission.status,
            AssignmentSubmission.submitted_at
        ).filter(
            AssignmentSubmission.student_id == current_user_id,
            AssignmentSubmission.assignment_id.in_(assignment_ids)
        ).all()
        sub_map = {aid: {'status': status, 'submitted_at': (submitted_at.isoformat() if submitted_at else None)} for aid, status, submitted_at in submissions}
    
    return jsonify([{
        'id': assignment.id,
        'title': assignment.title,
        'description': assignment.description,
        'due_date': assignment.due_date.isoformat(),
        'max_points': float(assignment.max_points),
        'allow_late_submissions': assignment.allow_late_submissions,
        'is_archived': assignment.is_archived,
        'created_at': assignment.created_at.isoformat(),
        **({'submission': sub_map.get(assignment.id)} if user and user.role == 'student' else {})
    } for assignment in assignments])

@app.route('/api/courses/<int:course_id>/assignments', methods=['POST'])
@jwt_required()
@role_required(['teacher', 'admin'])
def create_assignment(course_id):
    data = request.get_json()
    current_user_id = int(get_jwt_identity())
    
    # Verificar que el usuario sea el profesor del curso
    course = Course.query.get_or_404(course_id)
    if course.teacher_id != current_user_id:
        return jsonify({'message': 'No tienes permisos para crear tareas en este curso'}), 403
    
    assignment = Assignment(
        title=data['title'],
        description=data.get('description', ''),
        due_date=datetime.fromisoformat((data['due_date'] or '').replace('Z', '+00:00')),
        max_points=data.get('max_points', 100),
        allow_late_submissions=data.get('allow_late_submissions', True),
        course_id=course_id
    )
    
    try:
        db.session.add(assignment)
        db.session.commit()
        
        # Crear notificaciones para todos los estudiantes del curso
        students = query_all(
            "SELECT student_id FROM course_enrollments WHERE course_id = %s",
            (course_id,)
        )
        
        for student in students:
            create_notification(
                user_id=student['student_id'],
                title=f"Nueva tarea: {assignment.title}",
                message=f"Se ha creado una nueva tarea en {course.name}. Fecha límite: {assignment.due_date.strftime('%d/%m/%Y %H:%M')}",
                notification_type='assignment',
                related_id=assignment.id
            )
        
        return jsonify({
            'message': 'Tarea creada exitosamente',
            'assignment': {
                'id': assignment.id,
                'title': assignment.title
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al crear tarea'}), 500

# Actualizar tarea (solo profesor dueño)
@app.route('/api/assignments/<int:assignment_id>', methods=['PUT'])
@jwt_required()
@role_required(['teacher', 'admin'])
def update_assignment(assignment_id):
    data = request.get_json() or {}
    current_user_id = int(get_jwt_identity())
    assignment = Assignment.query.get_or_404(assignment_id)
    # owner check
    if assignment.course.teacher_id != current_user_id:
        return jsonify({'message': 'No tienes permisos para editar esta tarea'}), 403
    # update fields
    assignment.title = data.get('title', assignment.title)
    assignment.description = data.get('description', assignment.description)
    if 'due_date' in data and data['due_date']:
        assignment.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
    if 'max_points' in data:
        assignment.max_points = data.get('max_points')
    if 'allow_late_submissions' in data:
        assignment.allow_late_submissions = data.get('allow_late_submissions')
    try:
        db.session.commit()
        return jsonify({'message': 'Tarea actualizada'}), 200
    except Exception:
        db.session.rollback()
        return jsonify({'message': 'Error al actualizar tarea'}), 500

# Archivar/Desarchivar tarea (solo profesor dueño)
@app.route('/api/assignments/<int:assignment_id>/archive', methods=['PUT'])
@jwt_required()
@role_required(['teacher', 'admin'])
def archive_assignment(assignment_id):
    data = request.get_json() or {}
    current_user_id = int(get_jwt_identity())
    assignment = Assignment.query.get_or_404(assignment_id)
    if assignment.course.teacher_id != current_user_id:
        return jsonify({'message': 'No tienes permisos para archivar esta tarea'}), 403
    assignment.is_archived = bool(data.get('is_archived', True))
    try:
        db.session.commit()
        return jsonify({'message': 'Estado de archivo actualizado', 'is_archived': assignment.is_archived}), 200
    except Exception:
        db.session.rollback()
        return jsonify({'message': 'Error al actualizar estado de archivo'}), 500

# Borrar tarea (solo profesor dueño)
@app.route('/api/assignments/<int:assignment_id>', methods=['DELETE'])
@jwt_required()
@role_required(['teacher', 'admin'])
def delete_assignment(assignment_id):
    current_user_id = int(get_jwt_identity())
    assignment = Assignment.query.get_or_404(assignment_id)
    if assignment.course.teacher_id != current_user_id:
        return jsonify({'message': 'No tienes permisos para borrar esta tarea'}), 403
    try:
        db.session.delete(assignment)
        db.session.commit()
        return jsonify({'message': 'Tarea eliminada'}), 200
    except Exception:
        db.session.rollback()
        return jsonify({'message': 'Error al eliminar tarea'}), 500

# Rutas de gestión de entregas
@app.route('/api/assignments/<int:assignment_id>/submissions', methods=['POST'])
@jwt_required()
@role_required(['student'])
def submit_assignment(assignment_id):
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Verificar si ya existe una entrega
    existing_submission = AssignmentSubmission.query.filter_by(
        student_id=current_user_id,
        assignment_id=assignment_id
    ).first()
    
    if existing_submission:
        # Actualizar entrega existente
        existing_submission.content = data.get('content', '')
        existing_submission.status = 'submitted'
        existing_submission.submitted_at = datetime.utcnow()
        
        # Verificar si es tarde
        if existing_submission.submitted_at > assignment.due_date:
            existing_submission.status = 'late'
    else:
        # Crear nueva entrega
        submission = AssignmentSubmission(
            student_id=current_user_id,
            assignment_id=assignment_id,
            content=data.get('content', ''),
            status='submitted',
            submitted_at=datetime.utcnow()
        )
        
        # Verificar si es tarde
        if submission.submitted_at > assignment.due_date:
            submission.status = 'late'
        
        db.session.add(submission)
    
    try:
        db.session.commit()
        # Responder con el objeto de entrega (creado o actualizado)
        target = existing_submission if existing_submission else submission
        return jsonify({
            'id': target.id,
            'student_id': target.student_id,
            'assignment_id': target.assignment_id,
            'content': target.content,
            'status': target.status,
            'submitted_at': target.submitted_at.isoformat() if target.submitted_at else None,
            'points_earned': float(target.points_earned) if target.points_earned else None,
            'feedback': target.feedback,
            'created_at': target.created_at.isoformat()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al enviar entrega'}), 500

@app.route('/api/assignments/<int:assignment_id>/my-submission', methods=['GET'])
@jwt_required()
@role_required(['student'])
def get_my_submission(assignment_id):
    current_user_id = int(get_jwt_identity())
    Assignment.query.get_or_404(assignment_id)
    sub = AssignmentSubmission.query.filter_by(
        assignment_id=assignment_id,
        student_id=current_user_id
    ).first()
    if not sub:
        return jsonify(None)
    return jsonify({
        'id': sub.id,
        'student_id': sub.student_id,
        'assignment_id': sub.assignment_id,
        'content': sub.content,
        'status': sub.status,
        'submitted_at': sub.submitted_at.isoformat() if sub.submitted_at else None,
        'points_earned': float(sub.points_earned) if sub.points_earned else None,
        'feedback': sub.feedback,
        'created_at': sub.created_at.isoformat()
    })

# Rutas de calificaciones
@app.route('/api/submissions/<int:submission_id>/grade', methods=['POST'])
@jwt_required()
@role_required(['teacher', 'admin'])
def grade_submission(submission_id):
    data = request.get_json()
    current_user_id = int(get_jwt_identity())
    
    submission = AssignmentSubmission.query.get_or_404(submission_id)
    
    # Verificar que el usuario sea el profesor del curso
    if submission.assignment.course.teacher_id != current_user_id:
        return jsonify({'message': 'No tienes permisos para calificar esta entrega'}), 403
    
    submission.points_earned = data.get('points_earned')
    submission.feedback = data.get('feedback', '')
    submission.graded_by = current_user_id
    submission.graded_at = datetime.utcnow()
    submission.status = 'graded'
    
    try:
        db.session.commit()
        return jsonify({'message': 'Calificación guardada exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al guardar calificación'}), 500

# Rutas adicionales para detalles
@app.route('/api/courses/<int:course_id>', methods=['GET'])
@jwt_required()
def get_course_detail(course_id):
    try:
        current_user_id = int(get_jwt_identity())
        
        # Buscar el curso con información del profesor
        course = query_one("""
            SELECT c.*, u.first_name, u.last_name, u.email
            FROM courses c
            JOIN users u ON u.id = c.teacher_id
            WHERE c.id = %s
        """, (course_id,))
        
        if not course:
            return jsonify({'message': 'Curso no encontrado'}), 404
        
        # Verificar acceso al curso
        has_access = False
        
        # Verificar si es el profesor del curso
        if course['teacher_id'] == current_user_id:
            has_access = True
        else:
            # Verificar si el usuario está inscrito como estudiante
            enrollment = query_one("""
                SELECT id FROM course_enrollments 
                WHERE student_id = %s AND course_id = %s
            """, (current_user_id, course_id))
            if enrollment:
                has_access = True
        
        if not has_access:
            return jsonify({'message': 'No tienes acceso a este curso'}), 403
        
        # Contar estudiantes inscritos en el curso
        students_count = query_one("""
            SELECT COUNT(*) as count FROM course_enrollments 
            WHERE course_id = %s
        """, (course_id,))['count']
        
        return jsonify({
            'id': course['id'],
            'name': course['name'],
            'description': course['description'],
            'section': course['section'],
            'subject': course['subject'],
            'room': course['room'],
            'access_code': course['access_code'],
            'is_active': bool(course['is_active']) if course['is_active'] is not None else True,
            'teacher': {
                'id': course['teacher_id'],
                'first_name': course['first_name'],
                'last_name': course['last_name'],
                'email': course['email']
            },
            'students_count': students_count,
            'created_at': course['created_at'].isoformat() if course['created_at'] else None
        })
        
    except Exception as e:
        print(f"Error en get_course_detail: {e}")
        return jsonify({'message': 'Error al obtener detalles del curso'}), 500

@app.route('/api/assignments/<int:assignment_id>', methods=['GET'])
@jwt_required()
def get_assignment_detail(assignment_id):
    try:
        current_user_id = int(get_jwt_identity())
        
        # Buscar la tarea
        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            return jsonify({'message': 'Tarea no encontrada'}), 404
        
        # Verificar acceso a la tarea
        has_access = False
        
        # Verificar si es el profesor del curso
        if assignment.course.teacher_id == current_user_id:
            has_access = True
        else:
            # Verificar si el usuario está inscrito en el curso
            enrollment = CourseEnrollment.query.filter_by(
                student_id=current_user_id,
                course_id=assignment.course_id
            ).first()
            if enrollment:
                has_access = True
        
        if not has_access:
            return jsonify({'message': 'No tienes acceso a esta tarea'}), 403
        
        # Obtener información del curso
        course = assignment.course
        
        return jsonify({
            'id': assignment.id,
            'title': assignment.title,
            'description': assignment.description,
            'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
            'max_points': float(assignment.max_points) if assignment.max_points else 0.0,
            'allow_late_submissions': assignment.allow_late_submissions,
            'is_archived': assignment.is_archived,
            'course': {
                'id': course.id,
                'name': course.name,
                'subject': course.subject,
                'section': course.section
            },
            'created_at': assignment.created_at.isoformat() if assignment.created_at else None
        })
        
    except Exception as e:
        return jsonify({'message': 'Error al obtener detalles de la tarea'}), 500

@app.route('/api/assignments/<int:assignment_id>/submissions', methods=['GET'])
@jwt_required()
@role_required(['teacher', 'admin'])
def get_assignment_submissions(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    current_user_id = int(get_jwt_identity())
    
    # Verificar que el usuario sea el profesor del curso
    if assignment.course.teacher_id != current_user_id:
        return jsonify({'message': 'No tienes permisos para ver las entregas de esta tarea'}), 403
    
    submissions = AssignmentSubmission.query.filter_by(assignment_id=assignment_id).all()
    
    return jsonify([{
        'id': submission.id,
        'student': {
            'id': submission.student.id,
            'first_name': submission.student.first_name,
            'last_name': submission.student.last_name,
            'email': submission.student.email
        },
        'content': submission.content,
        'points_earned': float(submission.points_earned) if submission.points_earned else None,
        'feedback': submission.feedback,
        'status': submission.status,
        'submitted_at': submission.submitted_at.isoformat() if submission.submitted_at else None,
        'graded_at': submission.graded_at.isoformat() if submission.graded_at else None,
        'created_at': submission.created_at.isoformat()
    } for submission in submissions])

# Rutas de gestión de anuncios
@app.route('/api/courses/<int:course_id>/announcements', methods=['GET'])
@jwt_required()
def get_announcements(course_id):
    announcements = Announcement.query.filter_by(course_id=course_id).order_by(Announcement.created_at.desc()).all()
    
    return jsonify([{
        'id': announcement.id,
        'title': announcement.title,
        'content': announcement.content,
        'is_pinned': announcement.is_pinned,
        'author': {
            'id': announcement.author.id,
            'first_name': announcement.author.first_name,
            'last_name': announcement.author.last_name
        },
        'created_at': announcement.created_at.isoformat()
    } for announcement in announcements])

@app.route('/api/courses/<int:course_id>/announcements', methods=['POST'])
@jwt_required()
@role_required(['teacher', 'admin'])
def create_announcement(course_id):
    data = request.get_json()
    current_user_id = int(get_jwt_identity())
    
    # Verificar que el usuario sea el profesor del curso
    course = Course.query.get_or_404(course_id)
    if course.teacher_id != current_user_id:
        return jsonify({'message': 'No tienes permisos para crear anuncios en este curso'}), 403
    
    announcement = Announcement(
        title=data['title'],
        content=data['content'],
        is_pinned=data.get('is_pinned', False),
        course_id=course_id,
        author_id=current_user_id
    )
    
    try:
        db.session.add(announcement)
        db.session.commit()
        
        return jsonify({
            'message': 'Anuncio creado exitosamente',
            'announcement': {
                'id': announcement.id,
                'title': announcement.title
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al crear anuncio'}), 500

# Rutas de gestión de comentarios
@app.route('/api/announcements/<int:announcement_id>/comments', methods=['GET'])
@jwt_required()
def get_announcement_comments(announcement_id):
    comments = Comment.query.filter_by(announcement_id=announcement_id).order_by(Comment.created_at.asc()).all()
    
    return jsonify([{
        'id': comment.id,
        'content': comment.content,
        'author': {
            'id': comment.author.id,
            'first_name': comment.author.first_name,
            'last_name': comment.author.last_name
        },
        'created_at': comment.created_at.isoformat()
    } for comment in comments])

@app.route('/api/announcements/<int:announcement_id>/comments', methods=['POST'])
@jwt_required()
def create_announcement_comment(announcement_id):
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    comment = Comment(
        content=data['content'],
        author_id=current_user_id,
        announcement_id=announcement_id
    )
    
    try:
        db.session.add(comment)
        db.session.commit()
        
        return jsonify({
            'message': 'Comentario creado exitosamente',
            'comment': {
                'id': comment.id,
                'content': comment.content
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al crear comentario'}), 500

# Rutas de mensajería privada
@app.route('/api/messages', methods=['GET'])
@jwt_required()
def get_messages():
    current_user_id = get_jwt_identity()
    messages = Message.query.filter(
        (Message.sender_id == current_user_id) | (Message.receiver_id == current_user_id)
    ).order_by(Message.created_at.desc()).all()
    
    return jsonify([{
        'id': message.id,
        'sender': {
            'id': message.sender.id,
            'first_name': message.sender.first_name,
            'last_name': message.sender.last_name
        },
        'receiver': {
            'id': message.receiver.id,
            'first_name': message.receiver.first_name,
            'last_name': message.receiver.last_name
        },
        'subject': message.subject,
        'content': message.content,
        'is_read': message.is_read,
        'created_at': message.created_at.isoformat()
    } for message in messages])

@app.route('/api/messages', methods=['POST'])
@jwt_required()
def send_message():
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    message = Message(
        sender_id=current_user_id,
        receiver_id=data['receiver_id'],
        subject=data.get('subject', ''),
        content=data['content']
    )
    
    try:
        db.session.add(message)
        db.session.commit()
        
        return jsonify({
            'message': 'Mensaje enviado exitosamente',
            'message_id': message.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al enviar mensaje'}), 500

@app.route('/api/messages/<int:message_id>/read', methods=['PUT'])
@jwt_required()
def mark_message_read(message_id):
    current_user_id = get_jwt_identity()
    message = Message.query.filter_by(
        id=message_id,
        receiver_id=current_user_id
    ).first_or_404()
    
    message.is_read = True
    
    try:
        db.session.commit()
        return jsonify({'message': 'Mensaje marcado como leído'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al actualizar mensaje'}), 500

# Rutas para estudiantes de un curso
@app.route('/api/courses/<int:course_id>/students', methods=['GET'])
@jwt_required()
@role_required(['teacher', 'admin'])
def get_course_students(course_id):
    course = Course.query.get_or_404(course_id)
    current_user_id = int(get_jwt_identity())
    
    # Verificar que el usuario sea el profesor del curso
    if course.teacher_id != current_user_id:
        return jsonify({'message': 'No tienes permisos para ver los estudiantes de este curso'}), 403
    
    enrollments = CourseEnrollment.query.filter_by(course_id=course_id).all()
    
    return jsonify([{
        'id': enrollment.student.id,
        'first_name': enrollment.student.first_name,
        'last_name': enrollment.student.last_name,
        'email': enrollment.student.email,
        'enrolled_at': enrollment.enrolled_at.isoformat()
    } for enrollment in enrollments])

# Rutas para manejo de archivos
@app.route('/api/files/upload', methods=['POST'])
@jwt_required()
def upload_file():
    current_user_id = int(get_jwt_identity())
    
    if 'file' not in request.files:
        return jsonify({'message': 'No se seleccionó ningún archivo'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No se seleccionó ningún archivo'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'message': 'Tipo de archivo no permitido'}), 400
    
    try:
        # Generar nombre único para el archivo
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        # Guardar archivo
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Obtener información del archivo
        file_size = os.path.getsize(file_path)
        
        # Detectar tipo MIME usando múltiples métodos
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            # Fallback: detectar por extensión
            file_extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
            mime_type = get_mime_type_by_extension(file_extension)
        
        # Obtener IDs opcionales de la request
        submission_id = request.form.get('submission_id')
        assignment_id = request.form.get('assignment_id')
        announcement_id = request.form.get('announcement_id')
        
        # Crear registro en la base de datos
        attachment = FileAttachment(
            filename=unique_filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            submission_id=int(submission_id) if submission_id else None,
            assignment_id=int(assignment_id) if assignment_id else None,
            announcement_id=int(announcement_id) if announcement_id else None,
            uploaded_by=current_user_id
        )
        
        db.session.add(attachment)
        db.session.commit()
        
        return jsonify({
            'message': 'Archivo subido exitosamente',
            'file': {
                'id': attachment.id,
                'filename': attachment.original_filename,
                'size': attachment.file_size,
                'mime_type': attachment.mime_type
            }
        }), 201
        
    except Exception as e:
        # Limpiar archivo si hay error
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'message': 'Error al subir archivo'}), 500

@app.route('/api/files/<int:file_id>', methods=['GET'])
@jwt_required()
def download_file(file_id):
    current_user_id = int(get_jwt_identity())
    
    attachment = FileAttachment.query.get_or_404(file_id)
    
    # Verificar permisos de acceso
    has_access = False
    
    if attachment.submission_id:
        # Verificar si es el estudiante que subió el archivo o el profesor del curso
        submission = AssignmentSubmission.query.get(attachment.submission_id)
        if submission:
            if submission.student_id == current_user_id:
                has_access = True
            elif submission.assignment.course.teacher_id == current_user_id:
                has_access = True
    
    elif attachment.assignment_id:
        # Verificar si es el profesor del curso o estudiante inscrito
        assignment = Assignment.query.get(attachment.assignment_id)
        if assignment:
            if assignment.course.teacher_id == current_user_id:
                has_access = True
            else:
                enrollment = CourseEnrollment.query.filter_by(
                    student_id=current_user_id,
                    course_id=assignment.course_id
                ).first()
                if enrollment:
                    has_access = True
    
    elif attachment.announcement_id:
        # Verificar acceso al anuncio
        announcement = Announcement.query.get(attachment.announcement_id)
        if announcement:
            if announcement.course.teacher_id == current_user_id:
                has_access = True
            else:
                enrollment = CourseEnrollment.query.filter_by(
                    student_id=current_user_id,
                    course_id=announcement.course_id
                ).first()
                if enrollment:
                    has_access = True
    
    if not has_access:
        return jsonify({'message': 'No tienes permisos para acceder a este archivo'}), 403
    
    if not os.path.exists(attachment.file_path):
        return jsonify({'message': 'Archivo no encontrado'}), 404
    
    return send_file(
        attachment.file_path,
        as_attachment=True,
        download_name=attachment.original_filename,
        mimetype=attachment.mime_type
    )

@app.route('/api/files/<int:file_id>', methods=['DELETE'])
@jwt_required()
def delete_file(file_id):
    current_user_id = int(get_jwt_identity())
    
    attachment = FileAttachment.query.get_or_404(file_id)
    
    # Verificar permisos (solo quien subió el archivo puede eliminarlo)
    if attachment.uploaded_by != current_user_id:
        return jsonify({'message': 'No tienes permisos para eliminar este archivo'}), 403
    
    try:
        # Eliminar archivo físico
        if os.path.exists(attachment.file_path):
            os.remove(attachment.file_path)
        
        # Eliminar registro de la base de datos
        db.session.delete(attachment)
        db.session.commit()
        
        return jsonify({'message': 'Archivo eliminado exitosamente'})
        
    except Exception as e:
        return jsonify({'message': 'Error al eliminar archivo'}), 500

@app.route('/api/files/<int:file_id>', methods=['PUT'])
@jwt_required()
def update_file(file_id):
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    try:
        # Buscar el archivo
        attachment = FileAttachment.query.get_or_404(file_id)
        
        # Verificar permisos (solo el que subió el archivo o admin/teacher)
        user = User.query.get(current_user_id)
        if attachment.uploaded_by != current_user_id and user.role not in ['admin', 'teacher']:
            return jsonify({'message': 'No tienes permisos para modificar este archivo'}), 403
        
        # Actualizar campos permitidos
        if 'assignment_id' in data:
            attachment.assignment_id = data['assignment_id']
        if 'submission_id' in data:
            attachment.submission_id = data['submission_id']
        if 'announcement_id' in data:
            attachment.announcement_id = data['announcement_id']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Archivo actualizado exitosamente',
            'file': {
                'id': attachment.id,
                'filename': attachment.original_filename,
                'assignment_id': attachment.assignment_id,
                'submission_id': attachment.submission_id,
                'announcement_id': attachment.announcement_id
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al actualizar archivo'}), 500

@app.route('/api/submissions/<int:submission_id>/files', methods=['GET'])
@jwt_required()
def get_submission_files(submission_id):
    current_user_id = int(get_jwt_identity())
    
    # Verificar acceso a la entrega
    submission = AssignmentSubmission.query.get_or_404(submission_id)
    
    # Verificar permisos
    if submission.student_id != current_user_id and submission.assignment.course.teacher_id != current_user_id:
        return jsonify({'message': 'No tienes permisos para ver estos archivos'}), 403
    
    files = FileAttachment.query.filter_by(submission_id=submission_id).all()
    
    return jsonify([{
        'id': file.id,
        'filename': file.original_filename,
        'size': file.file_size,
        'mime_type': file.mime_type,
        'uploaded_at': file.created_at.isoformat()
    } for file in files])

@app.route('/api/assignments/<int:assignment_id>/files', methods=['GET'])
@jwt_required()
def get_assignment_files(assignment_id):
    current_user_id = int(get_jwt_identity())
    
    # Verificar acceso a la tarea
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Verificar permisos
    if assignment.course.teacher_id != current_user_id:
        # Verificar si el usuario está inscrito en el curso
        enrollment = CourseEnrollment.query.filter_by(
            student_id=current_user_id,
            course_id=assignment.course_id
        ).first()
        if not enrollment:
            return jsonify({'message': 'No tienes permisos para ver estos archivos'}), 403
    
    files = FileAttachment.query.filter_by(assignment_id=assignment_id).all()
    
    return jsonify([{
        'id': file.id,
        'filename': file.original_filename,
        'size': file.file_size,
        'mime_type': file.mime_type,
        'uploaded_at': file.created_at.isoformat()
    } for file in files])

# Rutas de notificaciones
@app.route('/api/notifications', methods=['GET'])
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

@app.route('/api/notifications/<int:notification_id>/read', methods=['PUT'])
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

@app.route("/api/health", methods=["GET"])
def health_check():
    return {"status": "ok"}, 200

@app.route('/api/notifications/read-all', methods=['PUT'])
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

# Función helper para crear notificaciones
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

# Eventos de WebSocket
@socketio.on('connect')
def handle_connect():
    print('Cliente conectado')

@socketio.on('disconnect')
def handle_disconnect():
    print('Cliente desconectado')

@socketio.on('join_user_room')
@jwt_required()
def handle_join_user_room(data):
    current_user_id = int(get_jwt_identity())
    join_room(f'user_{current_user_id}')
    print(f'Usuario {current_user_id} se unió a su sala')

@socketio.on('leave_user_room')
@jwt_required()
def handle_leave_user_room(data):
    current_user_id = int(get_jwt_identity())
    leave_room(f'user_{current_user_id}')
    print(f'Usuario {current_user_id} salió de su sala')

# Funciones para notificaciones por email
def send_assignment_notification(assignment_id, course_id):
    """Envía notificación por email cuando se crea una nueva tarea"""
    try:
        # Obtener información de la tarea y curso
        assignment = query_one("""
            SELECT a.*, c.name as course_name, u.first_name, u.last_name, u.email as teacher_email
            FROM assignments a
            JOIN courses c ON a.course_id = c.id
            JOIN users u ON c.teacher_id = u.id
            WHERE a.id = %s
        """, (assignment_id,))
        
        if not assignment:
            return False
        
        # Obtener estudiantes inscritos en el curso
        students = query_all("""
            SELECT u.email, u.first_name, u.last_name, u.assignment_reminders
            FROM course_enrollments ce
            JOIN users u ON ce.student_id = u.id
            WHERE ce.course_id = %s AND u.email_notifications = TRUE AND u.assignment_reminders = TRUE
        """, (course_id,))
        
        # Enviar notificación a cada estudiante
        for student in students:
            send_notification_email(
                student['email'],
                f"{student['first_name']} {student['last_name']}",
                'assignment',
                {
                    'title': assignment['title'],
                    'description': assignment['description'],
                    'due_date': assignment['due_date'].strftime('%d/%m/%Y %H:%M') if assignment['due_date'] else 'N/A',
                    'course_name': assignment['course_name'],
                    'teacher_name': f"{assignment['first_name']} {assignment['last_name']}"
                }
            )
        
        return True
    except Exception as e:
        print(f"Error enviando notificación de tarea: {e}")
        return False

def send_grade_notification(submission_id):
    """Envía notificación por email cuando se califica una tarea"""
    try:
        # Obtener información de la calificación
        submission = query_one("""
            SELECT s.*, a.title as assignment_title, u.email, u.first_name, u.last_name, u.grade_notifications
            FROM assignment_submissions s
            JOIN assignments a ON s.assignment_id = a.id
            JOIN users u ON s.student_id = u.id
            WHERE s.id = %s AND u.email_notifications = TRUE AND u.grade_notifications = TRUE
        """, (submission_id,))
        
        if not submission or not submission['grade_notifications']:
            return False
        
        send_notification_email(
            submission['email'],
            f"{submission['first_name']} {submission['last_name']}",
            'grade',
            {
                'assignment_title': submission['assignment_title'],
                'grade': submission['points_earned'],
                'comments': submission['feedback'] or 'Sin comentarios'
            }
        )
        
        return True
    except Exception as e:
        print(f"Error enviando notificación de calificación: {e}")
        return False

def send_announcement_notification(announcement_id, course_id):
    """Envía notificación por email cuando se crea un anuncio"""
    try:
        # Obtener información del anuncio
        announcement = query_one("""
            SELECT a.*, c.name as course_name
            FROM announcements a
            JOIN courses c ON a.course_id = c.id
            WHERE a.id = %s
        """, (announcement_id,))
        
        if not announcement:
            return False
        
        # Obtener estudiantes inscritos en el curso
        students = query_all("""
            SELECT u.email, u.first_name, u.last_name, u.announcement_notifications
            FROM course_enrollments ce
            JOIN users u ON ce.student_id = u.id
            WHERE ce.course_id = %s AND u.email_notifications = TRUE AND u.announcement_notifications = TRUE
        """, (course_id,))
        
        # Enviar notificación a cada estudiante
        for student in students:
            send_notification_email(
                student['email'],
                f"{student['first_name']} {student['last_name']}",
                'announcement',
                {
                    'title': announcement['title'],
                    'content': announcement['content'],
                    'course_name': announcement['course_name']
                }
            )
        
        return True
    except Exception as e:
        print(f"Error enviando notificación de anuncio: {e}")
        return False

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
