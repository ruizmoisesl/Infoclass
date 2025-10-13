import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configuración de la base de datos
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+mysqlconnector://root:password@localhost/infoclass_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 3,
        'max_overflow': 4
    }
    
    # Configuración JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 horas
    
    # Configuración de Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Configuración CORS para producción
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'https://infoclass-theta.vercel.app').split(',')
    
    # Configuración de archivos
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 10 * 1024 * 1024))  # 10MB
