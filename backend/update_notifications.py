#!/usr/bin/env python3
"""
Script para agregar la tabla de notificaciones a la base de datos
"""

import os
from sqlalchemy import create_engine, text
from config import Config

def update_notifications():
    """Agregar la tabla de notificaciones a la base de datos"""
    
    # Obtener URL de la base de datos
    database_url = os.getenv('DATABASE_URL', Config.SQLALCHEMY_DATABASE_URI)
    
    try:
        # Crear conexión a la base de datos
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            # Verificar si la tabla 'notifications' ya existe
            result = connection.execute(text("SHOW TABLES LIKE 'notifications'")).fetchone()
            if result:
                print("✅ La tabla 'notifications' ya existe")
                return

            # Si no existe, crearla
            print("📢 Creando tabla 'notifications'...")
            connection.execute(text("""
                CREATE TABLE notifications (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    is_read BOOLEAN DEFAULT FALSE,
                    related_id INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            """))
            
            # Crear índices
            connection.execute(text("CREATE INDEX idx_notifications_user ON notifications(user_id);"))
            connection.execute(text("CREATE INDEX idx_notifications_type ON notifications(type);"))
            connection.execute(text("CREATE INDEX idx_notifications_read ON notifications(is_read);"))
            
            connection.commit()
            print("✅ Tabla 'notifications' creada exitosamente")
            
    except Exception as e:
        print(f"❌ Error al actualizar la base de datos: {e}")

if __name__ == '__main__':
    update_notifications()
