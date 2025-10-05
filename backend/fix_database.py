#!/usr/bin/env python3
"""
Script para agregar la columna is_archived a la tabla assignments
"""

import os
import sys
from sqlalchemy import create_engine, text
from config import Config

def fix_database():
    """Agregar la columna is_archived a la tabla assignments"""
    
    # Obtener URL de la base de datos
    database_url = os.getenv('DATABASE_URL', Config.SQLALCHEMY_DATABASE_URI)
    
    try:
        # Crear conexión a la base de datos
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            # Verificar si la columna ya existe
            result = connection.execute(text("""
                SELECT COUNT(*) as count 
                FROM information_schema.columns 
                WHERE table_schema = DATABASE() 
                AND table_name = 'assignments' 
                AND column_name = 'is_archived'
            """))
            
            column_exists = result.fetchone()[0] > 0
            
            if column_exists:
                print("✅ La columna 'is_archived' ya existe en la tabla 'assignments'")
                return
            
            # Agregar la columna is_archived
            print("📁 Agregando columna 'is_archived' a la tabla 'assignments'...")
            
            connection.execute(text("""
                ALTER TABLE assignments 
                ADD COLUMN is_archived BOOLEAN DEFAULT FALSE
            """))
            
            connection.commit()
            print("✅ Columna 'is_archived' agregada exitosamente")
            
    except Exception as e:
        print(f"❌ Error al actualizar la base de datos: {e}")
        sys.exit(1)

if __name__ == '__main__':
    fix_database()
