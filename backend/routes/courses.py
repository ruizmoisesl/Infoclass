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


from models import (
    db as models_db,
    Course,
    CourseEnrollment,
)

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar la instancia de models.db con la app y usarla localmente como db
models_db.init_app(app)
db = models_db

courses_bp = Blueprint('courses', __name__)


@courses_bp.route('/api/courses', methods=['GET'])
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

@courses_bp.route('/api/courses', methods=['POST'])
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

@courses_bp.route('/api/courses/enroll', methods=['POST'])
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

@courses_bp.route('/api/courses/<int:course_id>/enroll', methods=['POST'])
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
