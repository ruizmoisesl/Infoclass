#!/usr/bin/env python3
"""
Script para verificar la estructura de las tablas
"""

from db import query_all

def check_table_structure():
    """Verifica la estructura de las tablas importantes"""
    try:
        print("🔍 Verificando estructura de tablas...")
        
        # Verificar assignment_submissions
        print("\n📋 Estructura de assignment_submissions:")
        try:
            result = query_all("DESCRIBE assignment_submissions")
            for row in result:
                print(f"  {row['Field']} - {row['Type']}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Verificar assignments
        print("\n📋 Estructura de assignments:")
        try:
            result = query_all("DESCRIBE assignments")
            for row in result:
                print(f"  {row['Field']} - {row['Type']}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Verificar si existe la columna grade
        print("\n🔍 Verificando columna 'grade' en assignment_submissions:")
        try:
            result = query_all("SELECT grade FROM assignment_submissions LIMIT 1")
            print("✅ Columna 'grade' existe")
        except Exception as e:
            print(f"❌ Columna 'grade' no existe: {e}")
        
        # Verificar si existe la columna is_archived
        print("\n🔍 Verificando columna 'is_archived' en assignments:")
        try:
            result = query_all("SELECT is_archived FROM assignments LIMIT 1")
            print("✅ Columna 'is_archived' existe")
        except Exception as e:
            print(f"❌ Columna 'is_archived' no existe: {e}")
        
    except Exception as e:
        print(f"❌ Error general: {e}")

if __name__ == "__main__":
    check_table_structure()
