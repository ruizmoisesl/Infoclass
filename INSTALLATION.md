# Guía de Instalación - InfoClass

Esta guía te ayudará a configurar y ejecutar InfoClass en tu máquina local.

## 📋 Prerrequisitos

Antes de comenzar, asegúrate de tener instalado:

- **Python 3.8+** - [Descargar Python](https://www.python.org/downloads/)
- **Node.js 16+** - [Descargar Node.js](https://nodejs.org/)
- **MySQL 8.0+** - [Descargar MySQL](https://dev.mysql.com/downloads/)
- **Git** - [Descargar Git](https://git-scm.com/downloads)

## 🚀 Instalación Paso a Paso

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/infoclass.git
cd infoclass
```

### 2. Configurar MySQL

#### 2.1. Instalar MySQL
- Descarga e instala MySQL desde el sitio oficial
- Durante la instalación, configura una contraseña para el usuario `root`
- Asegúrate de que MySQL esté ejecutándose como servicio

#### 2.2. Crear la Base de Datos

```bash
# Conectar a MySQL
mysql -u root -p

# Crear la base de datos
CREATE DATABASE infoclass_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Crear un usuario específico (opcional pero recomendado)
CREATE USER 'infoclass_user'@'localhost' IDENTIFIED BY 'tu_password_segura';
GRANT ALL PRIVILEGES ON infoclass_db.* TO 'infoclass_user'@'localhost';
FLUSH PRIVILEGES;

# Salir de MySQL
exit;
```

#### 2.3. Ejecutar el Script de Base de Datos

```bash
# Ejecutar el script SQL
mysql -u root -p infoclass_db < database_schema.sql
```

### 3. Configurar el Backend (Flask)

#### 3.1. Navegar al Directorio del Backend

```bash
cd backend
```

#### 3.2. Crear Entorno Virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate
```

#### 3.3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

#### 3.4. Configurar Variables de Entorno

Crear archivo `.env` en el directorio `backend/`:

```env
# Configuración de la base de datos
DATABASE_URL=mysql+pymysql://root:tu_password@localhost/infoclass_db

# Clave secreta para JWT (cambiar en producción)
JWT_SECRET_KEY=tu-clave-secreta-muy-segura-cambiar-en-produccion

# Configuración de Flask
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=tu-clave-secreta-para-flask
```

#### 3.5. Probar el Backend

```bash
python app.py
```

Si todo está correcto, deberías ver:
```
* Running on all addresses (0.0.0.0)
* Running on http://127.0.0.1:5000
* Running on http://[::1]:5000
```

### 4. Configurar el Frontend (React)

#### 4.1. Navegar al Directorio del Frontend

```bash
cd frontend
```

#### 4.2. Instalar Dependencias

```bash
npm install
```

#### 4.3. Configurar Variables de Entorno

Crear archivo `.env` en el directorio `frontend/`:

```env
# URL del backend
REACT_APP_API_URL=http://localhost:5000

# Configuración adicional (opcional)
GENERATE_SOURCEMAP=false
```

#### 4.4. Probar el Frontend

```bash
npm start
```

El frontend se abrirá automáticamente en `http://localhost:3000`

## 🔧 Solución de Problemas Comunes

### Error de Conexión a MySQL

**Problema**: `Can't connect to MySQL server`

**Solución**:
1. Verificar que MySQL esté ejecutándose
2. Verificar las credenciales en el archivo `.env`
3. Verificar que el puerto 3306 esté disponible

```bash
# Verificar estado de MySQL
# En Windows:
net start mysql
# En macOS/Linux:
sudo systemctl status mysql
```

### Error de Dependencias de Python

**Problema**: `ModuleNotFoundError`

**Solución**:
```bash
# Asegurarse de que el entorno virtual esté activado
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate

# Reinstalar dependencias
pip install -r requirements.txt
```

### Error de Dependencias de Node.js

**Problema**: `Module not found`

**Solución**:
```bash
# Limpiar caché y reinstalar
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### Error de CORS

**Problema**: `Access to fetch at 'http://localhost:5000' from origin 'http://localhost:3000' has been blocked by CORS policy`

**Solución**:
1. Verificar que Flask-CORS esté instalado
2. Verificar que la configuración de CORS esté correcta en `app.py`

### Error de Puerto en Uso

**Problema**: `Port 3000 is already in use`

**Solución**:
```bash
# Usar un puerto diferente
PORT=3001 npm start
```

## 🧪 Verificar la Instalación

### 1. Verificar Backend

Abrir `http://localhost:5000` en el navegador. Deberías ver una respuesta JSON o un mensaje de error (esto es normal si no hay rutas configuradas para la raíz).

### 2. Verificar Frontend

Abrir `http://localhost:3000` en el navegador. Deberías ver la página de login de InfoClass.

### 3. Verificar Base de Datos

```bash
# Conectar a MySQL
mysql -u root -p

# Verificar que la base de datos existe
SHOW DATABASES;

# Verificar las tablas
USE infoclass_db;
SHOW TABLES;

# Verificar datos de ejemplo
SELECT * FROM users;
```

## 🚀 Primeros Pasos

### 1. Crear Usuario Administrador

El script SQL ya incluye un usuario administrador por defecto:
- **Email**: admin@infoclass.com
- **Contraseña**: admin123

### 2. Crear Usuarios de Prueba

También se crean usuarios de ejemplo:
- **Profesor**: profesor@infoclass.com / admin123
- **Estudiante**: estudiante@infoclass.com / admin123

### 3. Probar la Aplicación

1. Abrir `http://localhost:3000`
2. Iniciar sesión con uno de los usuarios de prueba
3. Crear un curso (como profesor)
4. Inscribirse en el curso (como estudiante)
5. Crear una tarea y entregarla

## 📝 Configuración de Producción

### Variables de Entorno de Producción

```env
# Backend
DATABASE_URL=mysql+pymysql://usuario:password@host:puerto/database
JWT_SECRET_KEY=clave-super-segura-para-produccion
FLASK_ENV=production
FLASK_DEBUG=False

# Frontend
REACT_APP_API_URL=https://tu-backend.herokuapp.com
```

### Configuración de Base de Datos de Producción

1. Usar un servicio de base de datos en la nube (AWS RDS, Google Cloud SQL, etc.)
2. Configurar SSL para la conexión
3. Usar credenciales seguras
4. Configurar backups automáticos

## 🆘 Obtener Ayuda

Si encuentras problemas:

1. **Revisar los logs**: Verificar la consola del navegador y los logs del servidor
2. **Verificar la documentación**: Revisar el README.md principal
3. **Crear un issue**: Reportar problemas en GitHub
4. **Contactar al equipo**: Enviar un email al equipo de desarrollo

## 📚 Recursos Adicionales

- [Documentación de Flask](https://flask.palletsprojects.com/)
- [Documentación de React](https://reactjs.org/docs/)
- [Documentación de Tailwind CSS](https://tailwindcss.com/docs)
- [Documentación de MySQL](https://dev.mysql.com/doc/)

---

¡Felicitaciones! 🎉 Has configurado exitosamente InfoClass en tu máquina local.
