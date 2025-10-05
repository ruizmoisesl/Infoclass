#!/usr/bin/env python3
"""
Script de inicio para InfoClass Backend
"""

import os
import sys
from app import app, db

def create_tables():
    """Crear tablas de la base de datos si no existen"""
    with app.app_context():
        try:
            db.create_all()
            print("✅ Tablas de la base de datos creadas exitosamente")
        except Exception as e:
            print(f"❌ Error al crear tablas: {e}")
            sys.exit(1)

def check_database_connection():
    """Verificar conexión a la base de datos"""
    try:
        with app.app_context():
            db.engine.execute('SELECT 1')
            print("✅ Conexión a la base de datos exitosa")
            return True
    except Exception as e:
        print(f"❌ Error de conexión a la base de datos: {e}")
        print("💡 Asegúrate de que MySQL esté ejecutándose y las credenciales sean correctas")
        return False

def main():
    """Función principal"""
    print("🚀 Iniciando InfoClass Backend...")
    print("=" * 50)
    
    # Verificar variables de entorno
    required_vars = ['DATABASE_URL', 'JWT_SECRET_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Variables de entorno faltantes: {', '.join(missing_vars)}")
        print("💡 Crea un archivo .env con las variables necesarias")
        sys.exit(1)
    
    # Verificar conexión a la base de datos
    if not check_database_connection():
        sys.exit(1)
    
    # Crear tablas
    create_tables()
    
    # Iniciar servidor
    print("🌐 Iniciando servidor Flask...")
    print("📍 Backend disponible en: http://localhost:5000")
    print("📚 API Documentation: http://localhost:5000/api")
    print("=" * 50)
    
    app.run(
        debug=os.getenv('FLASK_DEBUG', 'True').lower() == 'true',
        host='0.0.0.0',
        port=5000
    )

if __name__ == '__main__':
    main()
