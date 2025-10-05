# InfoClass - Plataforma Educativa

Una plataforma educativa moderna similar a Google Classroom que permite a profesores crear y gestionar cursos, asignar tareas, calificar trabajos y comunicarse con los estudiantes.

## 🚀 Características Principales

### Para Profesores
- ✅ Crear y gestionar cursos con códigos de acceso únicos
- ✅ Crear tareas con fechas de entrega y puntuación
- ✅ Calificar entregas con feedback personalizado
- ✅ Crear anuncios y comunicarse con estudiantes
- ✅ Ver estadísticas de participación
- ✅ Gestionar estudiantes inscritos

### Para Estudiantes
- ✅ Inscribirse en cursos con código de acceso
- ✅ Ver todas las tareas asignadas
- ✅ Entregar trabajos con comentarios
- ✅ Recibir calificaciones y feedback
- ✅ Participar en discusiones
- ✅ Ver notificaciones de nuevas actividades

### Características Generales
- 🔐 Sistema de autenticación seguro con JWT
- 📱 Diseño responsive para móviles y escritorio
- 🎨 Interfaz moderna con Tailwind CSS
- 🔔 Sistema de notificaciones en tiempo real
- 📊 Dashboard con estadísticas personalizadas
- 💬 Sistema de mensajería privada
- 📝 Sistema de comentarios en tareas y anuncios

## 🛠️ Tecnologías Utilizadas

### Backend
- **Flask** - Framework web de Python
- **SQLAlchemy** - ORM para base de datos
- **MySQL** - Base de datos relacional
- **JWT** - Autenticación con tokens
- **Flask-CORS** - Manejo de CORS
- **bcrypt** - Encriptación de contraseñas

### Frontend
- **React 18** - Biblioteca de interfaz de usuario
- **React Router** - Enrutamiento del lado del cliente
- **Tailwind CSS** - Framework de CSS utilitario
- **Axios** - Cliente HTTP
- **Lucide React** - Iconos modernos
- **React Toastify** - Notificaciones toast
- **date-fns** - Manipulación de fechas

## 📋 Requisitos del Sistema

- Python 3.8+
- Node.js 16+
- MySQL 8.0+
- npm o yarn

## 🚀 Instalación y Configuración

### 1. Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/infoclass.git
cd infoclass
```

### 2. Configurar el Backend

```bash
# Navegar al directorio del backend
cd backend

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar la Base de Datos

```bash
# Crear base de datos MySQL
mysql -u root -p
CREATE DATABASE infoclass_db;
exit

# Ejecutar script de creación de tablas
mysql -u root -p infoclass_db < database_schema.sql
```

### 4. Configurar Variables de Entorno

Crear archivo `.env` en el directorio `backend/`:

```env
DATABASE_URL=mysql+pymysql://root:tu_password@localhost/infoclass_db
JWT_SECRET_KEY=tu-clave-secreta-muy-segura
FLASK_ENV=development
FLASK_DEBUG=True
```

### 5. Configurar el Frontend

```bash
# Navegar al directorio del frontend
cd frontend

# Instalar dependencias
npm install

# Crear archivo de configuración
echo "REACT_APP_API_URL=http://localhost:5000" > .env
```

## 🏃‍♂️ Ejecutar la Aplicación

### Backend
```bash
cd backend
python app.py
```
El backend estará disponible en `http://localhost:5000`

### Frontend
```bash
cd frontend
npm start
```
El frontend estará disponible en `http://localhost:3000`

## 📁 Estructura del Proyecto

```
infoclass/
├── backend/
│   ├── app.py                 # Aplicación principal Flask
│   ├── models.py               # Modelos de base de datos
│   ├── config.py            # Configuración de la aplicación
│   ├── requirements.txt     # Dependencias de Python
│   └── database_schema.sql # Script de creación de BD
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/     # Componentes reutilizables
│   │   ├── pages/         # Páginas de la aplicación
│   │   ├── contexts/      # Contextos de React
│   │   ├── api/           # Configuración de API
│   │   └── App.js         # Componente principal
│   ├── package.json
│   └── tailwind.config.js
└── README.md
```

## 🔧 API Endpoints

### Autenticación
- `POST /api/auth/register` - Registro de usuarios
- `POST /api/auth/login` - Inicio de sesión
- `GET /api/auth/me` - Información del usuario actual

### Cursos
- `GET /api/courses` - Listar cursos
- `POST /api/courses` - Crear curso
- `GET /api/courses/:id` - Detalles del curso
- `POST /api/courses/:id/enroll` - Inscribirse en curso

### Tareas
- `GET /api/courses/:id/assignments` - Tareas del curso
- `POST /api/courses/:id/assignments` - Crear tarea
- `GET /api/assignments/:id` - Detalles de tarea
- `POST /api/assignments/:id/submissions` - Entregar tarea

### Calificaciones
- `POST /api/submissions/:id/grade` - Calificar entrega

### Notificaciones
- `GET /api/notifications` - Listar notificaciones
- `PUT /api/notifications/:id/read` - Marcar como leída

## 🎨 Características de Diseño

- **Diseño Responsive**: Optimizado para móviles, tablets y escritorio
- **Paleta de Colores**: Colores primarios y secundarios consistentes
- **Tipografía**: Fuente Inter para mejor legibilidad
- **Iconografía**: Lucide React para iconos modernos
- **Animaciones**: Transiciones suaves y micro-interacciones
- **Accesibilidad**: Cumple estándares de accesibilidad web

## 🔒 Seguridad

- Autenticación JWT con tokens seguros
- Encriptación de contraseñas con bcrypt
- Validación de datos en frontend y backend
- Protección contra SQL injection
- Headers de seguridad CORS configurados
- Manejo seguro de sesiones

## 📊 Base de Datos

El sistema utiliza MySQL con las siguientes tablas principales:

- `users` - Información de usuarios
- `courses` - Cursos creados
- `course_enrollments` - Inscripciones de estudiantes
- `assignments` - Tareas asignadas
- `assignment_submissions` - Entregas de estudiantes
- `announcements` - Anuncios del curso
- `comments` - Comentarios en tareas y anuncios
- `messages` - Mensajería privada
- `notifications` - Notificaciones del sistema

## 🚀 Despliegue

### Backend (Heroku)
```bash
# Instalar Heroku CLI
# Crear app en Heroku
heroku create tu-app-backend

# Configurar variables de entorno
heroku config:set DATABASE_URL=tu_url_de_mysql
heroku config:set JWT_SECRET_KEY=tu_clave_secreta

# Desplegar
git push heroku main
```

### Frontend (Netlify/Vercel)
```bash
# Construir para producción
npm run build

# Desplegar en Netlify
netlify deploy --prod --dir=build
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 👥 Autores

- **Tu Nombre** - *Desarrollo inicial* - [tu-github](https://github.com/tu-github)

## 🙏 Agradecimientos

- Google Classroom por la inspiración
- La comunidad de React y Flask
- Todos los contribuidores de las librerías utilizadas

## 📞 Soporte

Si tienes preguntas o necesitas ayuda, puedes:

- Abrir un issue en GitHub
- Contactar al equipo de desarrollo
- Revisar la documentación de la API

---

**InfoClass** - Transformando la educación digital 🎓
