#!/usr/bin/env python3
"""
Script para probar el login y verificar contraseñas
"""

from db import query_one
import bcrypt

def test_login():
    """Prueba el proceso de login"""
    try:
        print("🔍 Probando proceso de login...")
        
        # Buscar usuario admin
        user = query_one(
            "SELECT id, email, password_hash, first_name, last_name, role FROM users WHERE email=%s",
            ('admin@infoclass.com',)
        )
        
        if not user:
            print("❌ Usuario admin no encontrado")
            return False
        
        print(f"✅ Usuario encontrado: {user['first_name']} {user['last_name']}")
        print(f"📧 Email: {user['email']}")
        print(f"🔑 Hash de contraseña: {user['password_hash'][:20]}...")
        
        # Probar diferentes contraseñas
        test_passwords = ['admin123', 'admin', 'password', '123456', 'admin@infoclass.com']
        
        for password in test_passwords:
            try:
                if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                    print(f"✅ Contraseña correcta: '{password}'")
                    return True
                else:
                    print(f"❌ Contraseña incorrecta: '{password}'")
            except Exception as e:
                print(f"❌ Error verificando contraseña '{password}': {e}")
        
        print("❌ Ninguna contraseña funcionó")
        return False
        
    except Exception as e:
        print(f"❌ Error en test_login: {e}")
        return False

def reset_admin_password():
    """Resetea la contraseña del admin"""
    try:
        print("🔄 Reseteando contraseña del admin...")
        
        # Generar nuevo hash para admin123
        new_password = "admin123"
        new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        from db import execute
        execute("UPDATE users SET password_hash = %s WHERE email = %s", (new_hash, 'admin@infoclass.com'))
        
        print("✅ Contraseña del admin reseteada a 'admin123'")
        return True
        
    except Exception as e:
        print(f"❌ Error reseteando contraseña: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando test de login...")
    
    # Primero probar login
    if not test_login():
        print("\n🔄 Intentando resetear contraseña...")
        if reset_admin_password():
            print("\n🔄 Probando login después del reset...")
            test_login()
