#!/usr/bin/env python3
"""
Script para actualizar la base de datos con los nuevos campos
"""

import os
import sys
from db import execute, query_one

def update_database():
    """Actualiza la base de datos con los nuevos campos"""
    
    print("🔄 Actualizando base de datos...")
    
    try:
        # Verificar si los campos ya existen
        print("📋 Verificando campos existentes...")
        
        # Verificar si email_verified existe
        try:
            query_one("SELECT email_verified FROM users LIMIT 1")
            print("✅ Campo email_verified ya existe")
        except:
            print("➕ Agregando campos de verificación de email...")
            execute("""
                ALTER TABLE users 
                ADD COLUMN email_verified BOOLEAN DEFAULT FALSE,
                ADD COLUMN verification_token VARCHAR(255) NULL,
                ADD COLUMN verification_token_expires TIMESTAMP NULL
            """)
            print("✅ Campos de verificación agregados")
        
        # Verificar si email_notifications existe
        try:
            query_one("SELECT email_notifications FROM users LIMIT 1")
            print("✅ Campo email_notifications ya existe")
        except:
            print("➕ Agregando campos de notificaciones...")
            execute("""
                ALTER TABLE users 
                ADD COLUMN email_notifications BOOLEAN DEFAULT TRUE,
                ADD COLUMN assignment_reminders BOOLEAN DEFAULT TRUE,
                ADD COLUMN grade_notifications BOOLEAN DEFAULT TRUE,
                ADD COLUMN announcement_notifications BOOLEAN DEFAULT TRUE
            """)
            print("✅ Campos de notificaciones agregados")
        
        # Verificar si bio existe
        try:
            query_one("SELECT bio FROM users LIMIT 1")
            print("✅ Campo bio ya existe")
        except:
            print("➕ Agregando campos de perfil...")
            execute("""
                ALTER TABLE users 
                ADD COLUMN bio TEXT NULL,
                ADD COLUMN phone VARCHAR(20) NULL,
                ADD COLUMN website VARCHAR(255) NULL,
                ADD COLUMN avatar VARCHAR(500) NULL
            """)
            print("✅ Campos de perfil agregados")
        
        # Crear índices si no existen
        try:
            execute("CREATE INDEX idx_verification_token ON users(verification_token)")
            print("✅ Índice de verificación creado")
        except:
            print("ℹ️ Índice de verificación ya existe")
        
        print("🎉 Base de datos actualizada exitosamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error actualizando base de datos: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando actualización de base de datos...")
    success = update_database()
    
    if success:
        print("✅ Actualización completada exitosamente")
        sys.exit(0)
    else:
        print("💥 Error en la actualización")
        sys.exit(1)