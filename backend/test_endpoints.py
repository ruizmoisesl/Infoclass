#!/usr/bin/env python3
"""
Script para probar los endpoints corregidos
"""

import requests
import json

def test_endpoints():
    """Prueba los endpoints principales"""
    base_url = "http://localhost:5000"
    
    print("🧪 Probando endpoints...")
    
    # 1. Probar login
    print("\n1️⃣ Probando login...")
    try:
        login_data = {
            "email": "admin@infoclass.com",
            "password": "admin123"
        }
        response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        if response.status_code == 200:
            token = response.json()['access_token']
            print("✅ Login exitoso")
        else:
            print(f"❌ Error en login: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error en login: {e}")
        return False
    
    # 2. Probar estadísticas
    print("\n2️⃣ Probando estadísticas...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{base_url}/api/users/stats", headers=headers)
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Estadísticas: {stats}")
        else:
            print(f"❌ Error en estadísticas: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error en estadísticas: {e}")
    
    # 3. Probar configuración de notificaciones
    print("\n3️⃣ Probando configuración de notificaciones...")
    try:
        response = requests.get(f"{base_url}/api/users/notification-settings", headers=headers)
        if response.status_code == 200:
            settings = response.json()
            print(f"✅ Configuración: {settings}")
        else:
            print(f"❌ Error en configuración: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error en configuración: {e}")
    
    # 4. Probar cursos
    print("\n4️⃣ Probando cursos...")
    try:
        response = requests.get(f"{base_url}/api/courses", headers=headers)
        if response.status_code == 200:
            courses = response.json()
            print(f"✅ Cursos obtenidos: {len(courses)} cursos")
        else:
            print(f"❌ Error en cursos: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error en cursos: {e}")
    
    print("\n🎉 Pruebas completadas!")

if __name__ == "__main__":
    test_endpoints()
