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
    Message
)

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar la instancia de models.db con la app y usarla localmente como db
models_db.init_app(app)
db = models_db

messages_bp = Blueprint('messages', __name__)

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
