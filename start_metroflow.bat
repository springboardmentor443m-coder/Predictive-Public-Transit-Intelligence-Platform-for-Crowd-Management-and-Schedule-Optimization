@echo off
echo ================================================================
echo   Launching MetroFlow AI Platform (Backend + Frontend)
echo   Exact Location: %~dp0
echo ================================================================
start "MetroFlow Backend [FastAPI]" cmd /k "call "%~dp0run_backend.bat""
timeout /t 3 /nobreak >nul
start "MetroFlow Frontend [Vite React]" cmd /k "call "%~dp0run_frontend.bat""
echo.
echo Both servers have been launched!
echo Access the application in your browser at:
echo   - Web Application: http://localhost:5173
echo   - Backend API Docs: http://127.0.0.1:8000/docs
echo ================================================================
timeout /t 5
