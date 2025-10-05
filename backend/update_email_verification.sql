-- Script para agregar campos de verificación de email a la tabla users

-- Agregar campos de verificación de email y perfil
ALTER TABLE users 
ADD COLUMN email_verified BOOLEAN DEFAULT FALSE,
ADD COLUMN verification_token VARCHAR(255) NULL,
ADD COLUMN verification_token_expires TIMESTAMP NULL,
ADD COLUMN email_notifications BOOLEAN DEFAULT TRUE,
ADD COLUMN assignment_reminders BOOLEAN DEFAULT TRUE,
ADD COLUMN grade_notifications BOOLEAN DEFAULT TRUE,
ADD COLUMN announcement_notifications BOOLEAN DEFAULT TRUE,
ADD COLUMN bio TEXT NULL,
ADD COLUMN phone VARCHAR(20) NULL,
ADD COLUMN website VARCHAR(255) NULL,
ADD COLUMN avatar VARCHAR(500) NULL;

-- Crear índice para el token de verificación
CREATE INDEX idx_verification_token ON users(verification_token);

-- Crear tabla para tokens de verificación (opcional, para mejor gestión)
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    token VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Crear índice para tokens
CREATE INDEX idx_email_verification_token ON email_verification_tokens(token);
CREATE INDEX idx_email_verification_user ON email_verification_tokens(user_id);
