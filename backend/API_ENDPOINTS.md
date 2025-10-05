# API Endpoints - InfoClass

## 🔐 Autenticación

### POST /api/auth/register
Registra un nuevo usuario y envía email de verificación.

**Body:**
```json
{
  "email": "usuario@ejemplo.com",
  "password": "contraseña123",
  "first_name": "Juan",
  "last_name": "Pérez",
  "role": "student"
}
```

**Response:**
```json
{
  "message": "Usuario creado exitosamente. Revisa tu email para verificar tu cuenta.",
  "access_token": "jwt_token",
  "user": {
    "id": 1,
    "email": "usuario@ejemplo.com",
    "first_name": "Juan",
    "last_name": "Pérez",
    "role": "student",
    "email_verified": false
  },
  "email_verification_sent": true
}
```

### POST /api/auth/verify-email
Verifica el email del usuario usando el token.

**Body:**
```json
{
  "token": "verification_token"
}
```

### POST /api/auth/resend-verification
Reenvía el email de verificación.

**Headers:** `Authorization: Bearer <token>`

## 👤 Perfil de Usuario

### GET /api/users/stats
Obtiene estadísticas del usuario actual.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "courses": 3,
  "assignments": 15,
  "submissions": 12,
  "average": 85.5
}
```

### GET /api/users/notification-settings
Obtiene la configuración de notificaciones del usuario.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "email_notifications": true,
  "assignment_reminders": true,
  "grade_notifications": true,
  "announcement_notifications": true
}
```

### PUT /api/users/notification-settings
Actualiza la configuración de notificaciones del usuario.

**Headers:** `Authorization: Bearer <token>`

**Body:**
```json
{
  "email_notifications": true,
  "assignment_reminders": false,
  "grade_notifications": true,
  "announcement_notifications": true
}
```

### PUT /api/users/profile
Actualiza el perfil del usuario.

**Headers:** `Authorization: Bearer <token>`

**Body:**
```json
{
  "first_name": "Juan",
  "last_name": "Pérez",
  "bio": "Estudiante de ingeniería",
  "phone": "+1234567890",
  "website": "https://juanperez.com"
}
```

**Response:**
```json
{
  "message": "Perfil actualizado exitosamente",
  "user": {
    "id": 1,
    "email": "usuario@ejemplo.com",
    "first_name": "Juan",
    "last_name": "Pérez",
    "role": "student",
    "bio": "Estudiante de ingeniería",
    "phone": "+1234567890",
    "website": "https://juanperez.com",
    "email_verified": true,
    "created_at": "2025-01-01T00:00:00"
  }
}
```

### PUT /api/users/password
Actualiza la contraseña del usuario.

**Headers:** `Authorization: Bearer <token>`

**Body:**
```json
{
  "current_password": "contraseña_actual",
  "new_password": "nueva_contraseña"
}
```

### POST /api/users/avatar
Sube un avatar para el usuario.

**Headers:** `Authorization: Bearer <token>`
**Content-Type:** `multipart/form-data`

**Body:** `avatar` (archivo de imagen)

**Response:**
```json
{
  "message": "Avatar actualizado exitosamente",
  "user": {
    "id": 1,
    "email": "usuario@ejemplo.com",
    "first_name": "Juan",
    "last_name": "Pérez",
    "role": "student",
    "avatar": "/uploads/avatars/avatar_1_abc123.jpg",
    "email_verified": true,
    "created_at": "2025-01-01T00:00:00"
  }
}
```

### DELETE /api/users/avatar
Elimina el avatar del usuario.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "message": "Avatar eliminado exitosamente",
  "user": {
    "id": 1,
    "email": "usuario@ejemplo.com",
    "first_name": "Juan",
    "last_name": "Pérez",
    "role": "student",
    "avatar": null,
    "email_verified": true,
    "created_at": "2025-01-01T00:00:00"
  }
}
```

## 📧 Sistema de Email

### Configuración SMTP
Para que el sistema de email funcione, configura estas variables en tu `.env`:

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=tu-email@gmail.com
MAIL_PASSWORD=tu-app-password
MAIL_DEFAULT_SENDER=tu-email@gmail.com
```

### Tipos de Notificaciones Automáticas

1. **Nuevas Tareas**: Se envían automáticamente cuando se crea una tarea
2. **Calificaciones**: Se envían cuando se califica una tarea
3. **Anuncios**: Se envían cuando se publica un anuncio
4. **Verificación**: Se envía al registrarse

## 🔧 Códigos de Estado

- `200`: Éxito
- `201`: Creado exitosamente
- `400`: Error en la solicitud
- `401`: No autorizado
- `403`: Prohibido
- `404`: No encontrado
- `500`: Error del servidor

## 📝 Notas Importantes

- Todos los endpoints de usuario requieren autenticación JWT
- Los archivos de avatar se almacenan en `/uploads/avatars/`
- Los tokens de verificación expiran en 24 horas
- Las notificaciones respetan las preferencias del usuario
- Los campos de perfil son opcionales
