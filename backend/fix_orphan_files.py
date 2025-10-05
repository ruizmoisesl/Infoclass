#!/usr/bin/env python3
"""
Script para corregir archivos huérfanos que no tienen assignment_id
"""

import os
from sqlalchemy import create_engine, text
from config import Config

def fix_orphan_files():
    """Corregir archivos huérfanos que no tienen assignment_id"""
    
    # Obtener URL de la base de datos
    database_url = os.getenv('DATABASE_URL', Config.SQLALCHEMY_DATABASE_URI)
    
    try:
        # Crear conexión a la base de datos
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            # Buscar archivos huérfanos (sin assignment_id, submission_id, announcement_id)
            result = connection.execute(text("""
                SELECT id, original_filename, uploaded_by, created_at
                FROM file_attachments 
                WHERE assignment_id IS NULL 
                AND submission_id IS NULL 
                AND announcement_id IS NULL
                ORDER BY created_at DESC
            """))
            
            orphan_files = result.fetchall()
            
            if not orphan_files:
                print("✅ No se encontraron archivos huérfanos")
                return
            
            print(f"📁 Se encontraron {len(orphan_files)} archivos huérfanos:")
            for file in orphan_files:
                print(f"  - ID: {file[0]}, Archivo: {file[1]}, Usuario: {file[2]}, Fecha: {file[3]}")
            
            # Preguntar si se desea eliminar
            response = input("\n¿Desea eliminar estos archivos huérfanos? (s/n): ")
            if response.lower() == 's':
                for file in orphan_files:
                    # Eliminar archivo físico si existe
                    file_path_result = connection.execute(text("""
                        SELECT file_path FROM file_attachments WHERE id = %s
                    """), (file[0],))
                    file_path = file_path_result.fetchone()
                    
                    if file_path and os.path.exists(file_path[0]):
                        try:
                            os.remove(file_path[0])
                            print(f"🗑️  Archivo físico eliminado: {file_path[0]}")
                        except Exception as e:
                            print(f"⚠️  Error eliminando archivo físico {file_path[0]}: {e}")
                    
                    # Eliminar registro de la base de datos
                    connection.execute(text("""
                        DELETE FROM file_attachments WHERE id = %s
                    """), (file[0],))
                    print(f"🗑️  Registro eliminado: ID {file[0]}")
                
                connection.commit()
                print("✅ Archivos huérfanos eliminados exitosamente")
            else:
                print("❌ Operación cancelada")
            
    except Exception as e:
        print(f"❌ Error al procesar archivos huérfanos: {e}")

if __name__ == '__main__':
    fix_orphan_files()
