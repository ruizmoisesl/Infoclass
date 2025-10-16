from flask import Flask, request, Blueprint, jsonify
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
from routes.notifications import create_notification

assignments_bp = Blueprint('assignments', __name__)

from models import (
    db as models_db,
    User,
    Course,
    CourseEnrollment,
    Assignment,
    AssignmentSubmission,
    Announcement,
)

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar la instancia de models.db con la app y usarla localmente como db
models_db.init_app(app)
db = models_db


   
# Rutas de gestión de tareas
@assignments_bp.route('/api/assignments', methods=['GET'])
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

@assignments_bp.route('/api/courses/<int:course_id>/assignments', methods=['GET'])
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

@assignments_bp.route('/api/courses/<int:course_id>/assignments', methods=['POST'])
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
@assignments_bp.route('/api/assignments/<int:assignment_id>', methods=['PUT'])
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
@assignments_bp.route('/api/assignments/<int:assignment_id>/archive', methods=['PUT'])
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
@assignments_bp.route('/api/assignments/<int:assignment_id>', methods=['DELETE'])
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
@assignments_bp.route('/api/assignments/<int:assignment_id>/submissions', methods=['POST'])
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

@assignments_bp.route('/api/assignments/<int:assignment_id>/my-submission', methods=['GET'])
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
@assignments_bp.route('/api/submissions/<int:submission_id>/grade', methods=['POST'])
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
@assignments_bp.route('/api/courses/<int:course_id>', methods=['GET'])
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

@assignments_bp.route('/api/assignments/<int:assignment_id>', methods=['GET'])
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

@assignments_bp.route('/api/assignments/<int:assignment_id>/submissions', methods=['GET'])
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
