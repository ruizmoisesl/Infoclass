#!/usr/bin/env python3
"""
Script para verificar usuarios en la base de datos
"""

from db import query_all, query_one

def check_users():
    """Verifica usuarios en la base de datos"""
    try:
        print("🔍 Verificando usuarios en la base de datos...")
        
        # Obtener todos los usuarios
        users = query_all("SELECT id, email, first_name, last_name, role FROM users")
        
        print(f"📊 Total de usuarios: {len(users)}")
        
        if users:
            print("\n👥 Usuarios encontrados:")
            for user in users:
                print(f"  - ID: {user['id']}, Email: {user['email']}, Nombre: {user['first_name']} {user['last_name']}, Rol: {user['role']}")
        else:
            print("❌ No hay usuarios en la base de datos")
            print("💡 Necesitas registrar un usuario primero")
        
        # Verificar estructura de la tabla
        print("\n🔧 Verificando estructura de la tabla...")
        try:
            # Probar consulta con nuevos campos
            test_user = query_one("SELECT id, email, password_hash, first_name, last_name, role, email_verified FROM users LIMIT 1")
            if test_user:
                print("✅ Estructura de tabla OK - nuevos campos disponibles")
            else:
                print("ℹ️ No hay usuarios para probar la estructura")
        except Exception as e:
            print(f"❌ Error en estructura de tabla: {e}")
        
        return len(users) > 0
        
    except Exception as e:
        print(f"❌ Error verificando usuarios: {e}")
        return False

if __name__ == "__main__":
    has_users = check_users()
    if not has_users:
        print("\n🚀 Para probar el login, primero registra un usuario en el frontend")
