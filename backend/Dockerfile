FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer el puerto (opcional, Railway lo maneja automáticamente)
EXPOSE 5000

# Comando de inicio en producción
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:${PORT}"]
