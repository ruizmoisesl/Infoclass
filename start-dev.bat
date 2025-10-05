@echo off
echo Iniciando InfoClass en modo desarrollo...
echo.

echo 1. Iniciando backend (Flask)...
start "Backend" cmd /k "cd backend && python app.py"

echo 2. Esperando 3 segundos para que el backend se inicie...
timeout /t 3 /nobreak > nul

echo 3. Iniciando frontend (React)...
start "Frontend" cmd /k "cd frontend && npm start"

echo.
echo ¡InfoClass iniciado exitosamente!
echo Backend: http://localhost:5000
echo Frontend: http://localhost:3000
echo.
pause
