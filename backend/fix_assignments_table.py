#!/usr/bin/env python3
"""
Script para agregar la columna is_archived a la tabla assignments
"""

from db import execute, query_one

def fix_assignments_table():
    """Agrega la columna is_archived a la tabla assignments"""
    try:
        print("🔧 Agregando columna is_archived a la tabla assignments...")
        
        # Verificar si la columna ya existe
        try:
            query_one("SELECT is_archived FROM assignments LIMIT 1")
            print("✅ Columna is_archived ya existe")
            return True
        except:
            print("➕ Agregando columna is_archived...")
        
        # Agregar la columna
        execute("ALTER TABLE assignments ADD COLUMN is_archived BOOLEAN DEFAULT FALSE")
        print("✅ Columna is_archived agregada exitosamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error agregando columna: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando fix de tabla assignments...")
    fix_assignments_table()
