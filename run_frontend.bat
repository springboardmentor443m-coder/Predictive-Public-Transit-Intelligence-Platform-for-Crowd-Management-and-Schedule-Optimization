@echo off
title MetroFlow Frontend UI
cd /d "%~dp0frontend"
echo ========================================================
echo   MetroFlow: Operations Command Center Frontend
echo   Running at: http://localhost:5173
echo ========================================================
npm run dev
pause
