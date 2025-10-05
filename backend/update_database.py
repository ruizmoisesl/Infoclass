#!/usr/bin/env python3
"""
Script para actualizar la base de datos con la nueva tabla de archivos
"""

import os
import sys
from sqlalchemy import create_engine, text
from config import Config

def update_database():
    """Actualizar la base de datos con la nueva tabla de archivos"""
    
    # Obtener URL de la base de datos
    database_url = os.getenv('DATABASE_URL', Config.SQLALCHEMY_DATABASE_URI)
    
    try:
        # Crear conexión a la base de datos
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            # Verificar si la tabla ya existe
            result = connection.execute(text("""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = 'file_attachments'
            """))
            
            table_exists = result.fetchone()[0] > 0
            
            if table_exists:
                print("✅ La tabla 'file_attachments' ya existe")
                return
            
            # Crear la tabla file_attachments
            print("📁 Creando tabla 'file_attachments'...")
            
            connection.execute(text("""
                CREATE TABLE file_attachments (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    filename VARCHAR(255) NOT NULL,
                    original_filename VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500) NOT NULL,
                    file_size BIGINT NOT NULL,
                    mime_type VARCHAR(100) NOT NULL,
                    submission_id INT,
                    assignment_id INT,
                    announcement_id INT,
                    uploaded_by INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (submission_id) REFERENCES assignment_submissions(id) ON DELETE CASCADE,
                    FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE,
                    FOREIGN KEY (announcement_id) REFERENCES announcements(id) ON DELETE CASCADE,
                    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE CASCADE
                )
            """))
            
            # Crear índices
            print("📊 Creando índices...")
            connection.execute(text("CREATE INDEX idx_files_submission ON file_attachments(submission_id)"))
            connection.execute(text("CREATE INDEX idx_files_assignment ON file_attachments(assignment_id)"))
            connection.execute(text("CREATE INDEX idx_files_uploader ON file_attachments(uploaded_by)"))
            
            # Crear directorio de uploads si no existe
            upload_dir = 'uploads'
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
                print(f"📁 Directorio '{upload_dir}' creado")
            
            connection.commit()
            print("✅ Base de datos actualizada exitosamente")
            
    except Exception as e:
        print(f"❌ Error al actualizar la base de datos: {e}")
        sys.exit(1)

if __name__ == '__main__':
    update_database()
