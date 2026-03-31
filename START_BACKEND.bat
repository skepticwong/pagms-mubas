@echo off
title PAGMS Backend Server
color 0B
echo ========================================
echo       PAGMS Backend Server
echo ========================================
echo.
echo Starting backend server on port 5000...
echo This window will show server output
echo.
echo Keep this window open while using the app
echo.
echo URL: http://localhost:5000
echo Health: http://localhost:5000/health
echo Auth: http://localhost:5000/api/me
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

cd /d "e:\Post-Award-Grant-Management-System-MUBAS (PAGMS)\pagms-mubas\backend"

python app.py

echo.
echo Backend server stopped.
pause
