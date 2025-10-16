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
    Comment
)

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar la instancia de models.db con la app y usarla localmente como db
models_db.init_app(app)
db = models_db

announcements_bp = Blueprint('announcements', __name__)


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
