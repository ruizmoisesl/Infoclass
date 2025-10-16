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
from routes import auth,users,courses,assignments
from routes.files import allowed_file
from routes.files import MAX_FILE_SIZE


app = Flask(__name__)
app.config.from_object(Config)

#Registrar Blueprints
app.register_blueprint(auth.auth_bp)
app.register_blueprint(users.users_bp)
app.register_blueprint(courses.courses_bp)
app.register_blueprint(assignments.assignments_bp)

# Inicializar Flask-Mail
mail = init_mail(app)
app.mail = mail

# Configuración para archivos
UPLOAD_FOLDER = 'uploads'


# Crear directorio de uploads si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE



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
CORS(app, origins=app.config['CORS_ORIGINS'])
socketio = SocketIO(app, cors_allowed_origins=app.config['CORS_ORIGINS'])

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
    # Crear tablas solo si el ORM aún se utiliza; ignorar errores si el esquema ya existe
    try:
        with app.app_context():
            db.create_all()
    except Exception:
        pass
    
    # Configuración de puerto para producción
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    socketio.run(app, debug=debug, host='0.0.0.0', port=port)
