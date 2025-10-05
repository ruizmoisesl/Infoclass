# Configuración del Sistema de Email - InfoClass

## 📧 Configuración de SMTP

Para que el sistema de notificaciones por email funcione, necesitas configurar las credenciales SMTP en tu archivo `.env`.

### 🔧 Variables de Entorno Requeridas

Agrega estas variables a tu archivo `.env`:

```env
# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=tu-email@gmail.com
MAIL_PASSWORD=tu-app-password
MAIL_DEFAULT_SENDER=tu-email@gmail.com
```

### 📋 Configuración por Proveedor

#### Gmail
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=tu-email@gmail.com
MAIL_PASSWORD=tu-app-password  # Usa App Password, no tu contraseña normal
```

**Importante para Gmail:**
1. Habilita la verificación en 2 pasos
2. Genera una "App Password" específica para esta aplicación
3. Usa la App Password como `MAIL_PASSWORD`

#### Outlook/Hotmail
```env
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
```

#### Yahoo
```env
MAIL_SERVER=smtp.mail.yahoo.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
```

## 🗄️ Actualización de la Base de Datos

Ejecuta el script SQL para agregar los campos de verificación de email:

```sql
-- Ejecutar en tu base de datos MySQL
source update_email_verification.sql
```

O ejecuta manualmente:

```sql
ALTER TABLE users 
ADD COLUMN email_verified BOOLEAN DEFAULT FALSE,
ADD COLUMN verification_token VARCHAR(255) NULL,
ADD COLUMN verification_token_expires TIMESTAMP NULL,
ADD COLUMN email_notifications BOOLEAN DEFAULT TRUE,
ADD COLUMN assignment_reminders BOOLEAN DEFAULT TRUE,
ADD COLUMN grade_notifications BOOLEAN DEFAULT TRUE,
ADD COLUMN announcement_notifications BOOLEAN DEFAULT TRUE;

CREATE INDEX idx_verification_token ON users(verification_token);
```

## 🚀 Funcionalidades Implementadas

### ✅ Verificación de Email
- **Registro**: Se envía automáticamente un email de verificación
- **Verificación**: Endpoint `/api/auth/verify-email` para verificar tokens
- **Reenvío**: Endpoint `/api/auth/resend-verification` para reenviar emails
- **Frontend**: Página `/verify-email/:token` para verificación automática

### ✅ Notificaciones por Email
- **Nuevas tareas**: Notificación automática a estudiantes inscritos
- **Calificaciones**: Notificación cuando se califica una tarea
- **Anuncios**: Notificación de nuevos anuncios en cursos
- **Configuración**: Los usuarios pueden configurar qué notificaciones recibir

### ✅ Templates de Email
- **Verificación**: Email HTML con diseño profesional
- **Notificaciones**: Templates específicos para cada tipo de notificación
- **Responsive**: Diseño que se adapta a diferentes dispositivos

## 🔧 Endpoints de API

### Autenticación
- `POST /api/auth/verify-email` - Verificar email con token
- `POST /api/auth/resend-verification` - Reenviar email de verificación

### Notificaciones (Automáticas)
- Se envían automáticamente cuando:
  - Se crea una nueva tarea
  - Se califica una tarea
  - Se publica un anuncio

## 🎨 Frontend

### Páginas Nuevas
- **VerifyEmail**: Página para verificar email con token
- **Profile**: Muestra estado de verificación y permite reenviar

### Funcionalidades
- Indicador visual de verificación de email
- Botón para reenviar verificación
- Configuración de notificaciones por email

## 🧪 Pruebas

### Probar Verificación de Email
1. Registra un nuevo usuario
2. Revisa el email recibido
3. Haz clic en el enlace de verificación
4. Verifica que el estado cambie a "verificado"

### Probar Notificaciones
1. Crea una nueva tarea en un curso
2. Verifica que los estudiantes reciban el email
3. Califica una tarea
4. Verifica que el estudiante reciba la notificación

## 🚨 Solución de Problemas

### Error: "No se pudo enviar email"
- Verifica las credenciales SMTP
- Asegúrate de usar App Password para Gmail
- Verifica que el puerto y TLS estén configurados correctamente

### Error: "Token de verificación inválido"
- El token puede haber expirado (24 horas)
- El usuario ya puede estar verificado
- Usa el botón "Reenviar verificación" en el perfil

### Emails no llegan
- Revisa la carpeta de spam
- Verifica que el dominio del remitente esté configurado correctamente
- Asegúrate de que el servidor SMTP esté funcionando

## 📝 Notas Importantes

- Los tokens de verificación expiran en 24 horas
- Los usuarios pueden desactivar notificaciones por email
- El sistema respeta las preferencias de notificación de cada usuario
- Los emails se envían de forma asíncrona para no bloquear la aplicación
