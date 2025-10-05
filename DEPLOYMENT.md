# Guía de Despliegue - InfoClass

Esta guía te ayudará a desplegar tu aplicación InfoClass en Vercel (frontend) y Railway/Render (backend).

## 🚀 Despliegue del Frontend en Vercel

### 1. Preparar el repositorio
```bash
# Asegúrate de que todos los cambios estén committeados
git add .
git commit -m "Preparar para despliegue en Vercel"
git push origin main
```

### 2. Conectar con Vercel
1. Ve a [vercel.com](https://vercel.com) y crea una cuenta
2. Haz clic en "New Project"
3. Conecta tu repositorio de GitHub
4. Selecciona el directorio `frontend` como raíz del proyecto
5. Configura las variables de entorno:
   - `REACT_APP_API_URL`: URL de tu backend desplegado (ej: `https://tu-backend.railway.app`)

### 3. Configuración automática
Vercel detectará automáticamente que es una aplicación React y usará la configuración del archivo `vercel.json`.

## 🔧 Despliegue del Backend

### Opción A: Railway (Recomendado)

1. Ve a [railway.app](https://railway.app) y crea una cuenta
2. Conecta tu repositorio de GitHub
3. Selecciona el directorio `backend`
4. Railway detectará automáticamente que es una aplicación Python
5. Configura las variables de entorno:
   - `DATABASE_URL`: URL de tu base de datos MySQL
   - `JWT_SECRET_KEY`: Clave secreta para JWT
   - `SECRET_KEY`: Clave secreta de Flask
   - `CORS_ORIGINS`: URL de tu frontend en Vercel
   - `FLASK_ENV`: `production`
   - `FLASK_DEBUG`: `false`

### Opción B: Render

1. Ve a [render.com](https://render.com) y crea una cuenta
2. Conecta tu repositorio de GitHub
3. Crea un nuevo "Web Service"
4. Selecciona el directorio `backend`
5. Configura las variables de entorno como en Railway

## 🗄️ Base de Datos

### Opción 1: Railway Database
1. En Railway, crea un nuevo servicio "Database"
2. Selecciona MySQL
3. Copia la URL de conexión y úsala como `DATABASE_URL`

### Opción 2: PlanetScale
1. Ve a [planetscale.com](https://planetscale.com)
2. Crea una nueva base de datos
3. Obtén la URL de conexión
4. Ejecuta el script `database_schema.sql` en tu base de datos

### Opción 3: MySQL en la nube
- **AWS RDS**
- **Google Cloud SQL**
- **Azure Database for MySQL**

## 📋 Variables de Entorno

### Frontend (Vercel)
```
REACT_APP_API_URL=https://tu-backend.railway.app
```

### Backend (Railway/Render)
```
DATABASE_URL=mysql://usuario:password@host:puerto/database
JWT_SECRET_KEY=tu-clave-secreta-muy-segura
SECRET_KEY=tu-clave-secreta-flask
CORS_ORIGINS=https://tu-frontend.vercel.app
FLASK_ENV=production
FLASK_DEBUG=false
PORT=5000
```

## 🔄 Flujo de Despliegue

1. **Despliega primero el backend** para obtener la URL
2. **Configura la base de datos** y obtén la URL de conexión
3. **Actualiza las variables de entorno** del backend con la URL de la base de datos
4. **Despliega el frontend** con la URL del backend
5. **Actualiza las variables de entorno** del backend con la URL del frontend

## 🧪 Verificación

1. **Backend**: Visita `https://tu-backend.railway.app/api/auth/me` (debería devolver 401, no 404)
2. **Frontend**: Visita `https://tu-frontend.vercel.app` (debería cargar la aplicación)
3. **Base de datos**: Verifica que las tablas se crearon correctamente

## 🐛 Solución de Problemas

### Error de CORS
- Verifica que `CORS_ORIGINS` incluya la URL exacta de tu frontend
- Asegúrate de que no haya espacios en blanco en las URLs

### Error de base de datos
- Verifica que la URL de la base de datos sea correcta
- Asegúrate de que la base de datos esté accesible desde internet
- Verifica que el usuario tenga permisos para crear tablas

### Error de archivos
- En producción, considera usar un servicio de almacenamiento como AWS S3 o Cloudinary
- Los archivos locales no persisten en Railway/Render

## 📚 Recursos Adicionales

- [Documentación de Vercel](https://vercel.com/docs)
- [Documentación de Railway](https://docs.railway.app)
- [Documentación de Render](https://render.com/docs)
- [Guía de CORS en Flask](https://flask-cors.readthedocs.io/)

