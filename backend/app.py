from flask import Flask, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
from flask_jwt_extended import JWTManager
import os
from config import Config
from db import query_one, query_all, execute
from email_config import init_mail, send_notification_email
from routes import auth_bp, users_bp, courses_bp, assignments_bp, notifications_bp, files_bp
from routes.files import MAX_FILE_SIZE


app = Flask(__name__)
app.config.from_object(Config)

#Registrar Blueprints para el funcionamiento de las rutas en el backend
app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)
app.register_blueprint(courses_bp)
app.register_blueprint(assignments_bp)
app.register_blueprint(notifications_bp)
app.register_blueprint(files_bp)


# Inicializar Flask-Mail
mail = init_mail(app)
app.mail = mail

# Configuración para archivos
UPLOAD_FOLDER = 'uploads'


# Inicializar jwt

jwt = JWTManager()


# Crear directorio de uploads si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE


# Inicialización de extensiones (usar la instancia de models.db)

CORS(app, origins=app.config['CORS_ORIGINS'])
socketio = SocketIO(app, cors_allowed_origins=app.config['CORS_ORIGINS'])
jwt.init_app(app)

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
    try:
        with app.app_context():
            db.create_all()
    except Exception:
        pass
    
    # Configuración de puerto para producción
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    socketio.run(app, debug=debug, host='0.0.0.0', port=port)
