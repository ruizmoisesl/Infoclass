#!/usr/bin/env python3
"""
Script para resetear contraseñas de usuarios existentes
"""

from db import query_all, execute
import bcrypt

def reset_user_passwords():
    """Resetea las contraseñas de todos los usuarios"""
    try:
        print("🔄 Reseteando contraseñas de usuarios...")
        
        # Obtener todos los usuarios
        users = query_all("SELECT id, email, first_name, last_name, role FROM users")
        
        # Contraseñas por defecto por rol
        default_passwords = {
            'admin': 'admin123',
            'teacher': 'teacher123', 
            'student': 'student123'
        }
        
        for user in users:
            role = user['role']
            default_password = default_passwords.get(role, 'password123')
            
            # Generar nuevo hash
            new_hash = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Actualizar en la base de datos
            execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, user['id']))
            
            print(f"✅ {user['first_name']} {user['last_name']} ({user['role']}) - Contraseña: {default_password}")
        
        print(f"\n🎉 Contraseñas reseteadas para {len(users)} usuarios")
        print("\n📋 Credenciales de prueba:")
        print("👤 Admin: admin@infoclass.com / admin123")
        print("👨‍🏫 Teacher: jeronimo@gmail.com / teacher123") 
        print("👨‍🎓 Student: moisesruiz2006m@gmail.com / student123")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reseteando contraseñas: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando reset de contraseñas...")
    reset_user_passwords()
