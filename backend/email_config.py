"""
Configuración para el sistema de email
"""
import os
from flask_mail import Mail, Message
from flask import current_app
import secrets
import string
from datetime import datetime, timedelta

# Configuración de email
MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', MAIL_USERNAME)

# Configuración de la aplicación
MAIL_SUBJECT_PREFIX = '[InfoClass] '
MAIL_SENDER = f'InfoClass <{MAIL_DEFAULT_SENDER}>'

def init_mail(app):
    """Inicializa Flask-Mail con la aplicación"""
    app.config['MAIL_SERVER'] = MAIL_SERVER
    app.config['MAIL_PORT'] = MAIL_PORT
    app.config['MAIL_USE_TLS'] = MAIL_USE_TLS
    app.config['MAIL_USE_SSL'] = MAIL_USE_SSL
    app.config['MAIL_USERNAME'] = MAIL_USERNAME
    app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
    app.config['MAIL_DEFAULT_SENDER'] = MAIL_DEFAULT_SENDER
    
    return Mail(app)

def generate_verification_token():
    """Genera un token de verificación único"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

def send_verification_email(user_email, user_name, verification_token):
    """Envía email de verificación de cuenta"""
    try:
        msg = Message(
            subject=f'{MAIL_SUBJECT_PREFIX}Verifica tu cuenta',
            recipients=[user_email],
            sender=MAIL_SENDER
        )
        
        # URL de verificación (ajustar según tu dominio)
        verification_url = f"https://infoclass-theta.vercel.app/verify-email?token={verification_token}"
        
        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Verifica tu cuenta - InfoClass</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>¡Bienvenido a InfoClass!</h1>
                </div>
                <div class="content">
                    <h2>Hola {user_name},</h2>
                    <p>Gracias por registrarte en InfoClass. Para completar tu registro y activar tu cuenta, necesitas verificar tu dirección de email.</p>
                    
                    <p>Haz clic en el siguiente botón para verificar tu cuenta:</p>
                    
                    <div style="text-align: center;">
                        <a href="{verification_url}" class="button">Verificar mi cuenta</a>
                    </div>
                    
                    <p>Si el botón no funciona, copia y pega este enlace en tu navegador:</p>
                    <p style="word-break: break-all; background: #eee; padding: 10px; border-radius: 5px;">{verification_url}</p>
                    
                    <p><strong>Importante:</strong> Este enlace expirará en 24 horas por seguridad.</p>
                    
                    <p>Si no creaste una cuenta en InfoClass, puedes ignorar este email.</p>
                </div>
                <div class="footer">
                    <p>© 2025 InfoClass. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        current_app.mail.send(msg)
        return True
    except Exception as e:
        print(f"Error enviando email de verificación: {e}")
        return False

def send_notification_email(user_email, user_name, notification_type, data):
    """Envía notificaciones por email según el tipo"""
    try:
        subject_map = {
            'assignment': 'Nueva tarea asignada',
            'grade': 'Nueva calificación disponible',
            'announcement': 'Nuevo anuncio',
            'message': 'Nuevo mensaje',
            'enrollment': 'Inscripción a curso'
        }
        
        msg = Message(
            subject=f'{MAIL_SUBJECT_PREFIX}{subject_map.get(notification_type, "Nueva notificación")}',
            recipients=[user_email],
            sender=MAIL_SENDER
        )
        
        # Generar contenido HTML según el tipo de notificación
        html_content = generate_notification_html(user_name, notification_type, data)
        msg.html = html_content
        
        current_app.mail.send(msg)
        return True
    except Exception as e:
        print(f"Error enviando notificación por email: {e}")
        return False

def generate_notification_html(user_name, notification_type, data):
    """Genera HTML para diferentes tipos de notificaciones"""
    base_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Notificación - InfoClass</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>InfoClass</h1>
            </div>
            <div class="content">
                <h2>Hola {user_name},</h2>
    """
    
    # Contenido específico según el tipo
    if notification_type == 'assignment':
        base_html += f"""
                <p>Se ha asignado una nueva tarea en el curso <strong>{data.get('course_name', 'N/A')}</strong>.</p>
                <h3>{data.get('title', 'Nueva tarea')}</h3>
                <p><strong>Descripción:</strong> {data.get('description', 'Sin descripción')}</p>
                <p><strong>Fecha límite:</strong> {data.get('due_date', 'N/A')}</p>
        """
    elif notification_type == 'grade':
        base_html += f"""
                <p>Tu calificación para la tarea <strong>{data.get('assignment_title', 'N/A')}</strong> está disponible.</p>
                <p><strong>Calificación:</strong> {data.get('grade', 'N/A')}</p>
                <p><strong>Comentarios:</strong> {data.get('comments', 'Sin comentarios')}</p>
        """
    elif notification_type == 'announcement':
        base_html += f"""
                <p>Hay un nuevo anuncio en el curso <strong>{data.get('course_name', 'N/A')}</strong>.</p>
                <h3>{data.get('title', 'Nuevo anuncio')}</h3>
                <p>{data.get('content', 'Sin contenido')}</p>
        """
    elif notification_type == 'message':
        base_html += f"""
                <p>Has recibido un nuevo mensaje de <strong>{data.get('sender_name', 'N/A')}</strong>.</p>
                <h3>{data.get('subject', 'Nuevo mensaje')}</h3>
                <p>{data.get('content', 'Sin contenido')}</p>
        """
    elif notification_type == 'enrollment':
        base_html += f"""
                <p>Te has inscrito exitosamente al curso <strong>{data.get('course_name', 'N/A')}</strong>.</p>
                <p><strong>Profesor:</strong> {data.get('teacher_name', 'N/A')}</p>
                <p><strong>Sección:</strong> {data.get('section', 'N/A')}</p>
        """
    
    base_html += """
                <p>¡Gracias por usar InfoClass!</p>
            </div>
            <div class="footer">
                <p>© 2025 InfoClass. Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return base_html
