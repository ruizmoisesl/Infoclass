#!/bin/bash

echo "Iniciando InfoClass en modo desarrollo..."
echo

echo "1. Iniciando backend (Flask)..."
cd backend
python app.py &
BACKEND_PID=$!

echo "2. Esperando 3 segundos para que el backend se inicie..."
sleep 3

echo "3. Iniciando frontend (React)..."
cd ../frontend
npm start &
FRONTEND_PID=$!

echo
echo "¡InfoClass iniciado exitosamente!"
echo "Backend: http://localhost:5000"
echo "Frontend: http://localhost:3000"
echo
echo "Presiona Ctrl+C para detener ambos servicios"

# Función para limpiar procesos al salir
cleanup() {
    echo "Deteniendo servicios..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit
}

# Capturar Ctrl+C
trap cleanup SIGINT

# Esperar a que termine cualquiera de los procesos
wait
