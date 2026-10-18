@echo off
title MetroFlow Backend Server
cd /d "%~dp0backend"
echo ========================================================
echo   MetroFlow: AI Transit Operations Backend Server
echo   Running at: http://127.0.0.1:8000
echo   Live WebSocket: ws://127.0.0.1:8000/ws/live
echo   API Docs: http://127.0.0.1:8000/docs
echo ========================================================
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
