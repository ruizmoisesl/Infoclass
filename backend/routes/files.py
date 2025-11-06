from flask import Flask, request, Blueprint, jsonify, send_file
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
from routes.roles import role_required
from utils import allowed_file
from routes.notifications import create_notification

from models import(
    db as models_db,
    FileAttachment,
    AssignmentSubmission,
    Assignment,
    Announcement,
    CourseEnrollment,
    User
)

# Inicializar la instancia de models.db con la app y usarla localmente como d

files_bp = Blueprint('files', __name__)

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

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Rutas para manejo de archivos
@files_bp.route('/api/files/upload', methods=['POST'])
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

@files_bp.route('/api/files/<int:file_id>', methods=['GET'])
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

@files_bp.route('/api/files/<int:file_id>', methods=['DELETE'])
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

@files_bp.route('/api/files/<int:file_id>', methods=['PUT'])
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
