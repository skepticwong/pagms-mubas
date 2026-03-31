@echo off
title PAGMS Development Servers
color 0A

echo ========================================
echo         PAGMS Development Servers
echo ========================================
echo.
echo This will start both backend and frontend servers
echo Backend will run on port 5000
echo Frontend will run on port 5173
echo.
echo Press Ctrl+C to stop servers
echo ========================================
echo.

echo [1/3] Starting Backend Server...
cd /d "e:\Post-Award-Grant-Management-System-MUBAS (PAGMS)\pagms-mubas\backend"

start "PAGMS Backend" cmd /k "echo Backend Server Running && python app.py"

echo.
echo [2/3] Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo.
echo [3/3] Testing Backend Connection...
curl -s http://localhost:5000/health
if %errorlevel% equ 0 (
    echo [OK] Backend is running!
) else (
    echo [ERROR] Backend failed to start
    pause
    exit /b 1
)

echo.
echo ========================================
echo         Servers Started Successfully
echo ========================================
echo.
echo Backend: http://localhost:5000
echo Frontend: http://localhost:5173
echo.
echo Opening frontend in browser...
start http://localhost:5173

echo.
echo Press any key to start frontend server...
pause >nul

cd /d "e:\Post-Award-Grant-Management-System-MUBAS (PAGMS)\pagms-mubas\frontend"
start "PAGMS Frontend" cmd /k "echo Frontend Server Running && npm run dev"

echo.
echo [OK] Both servers are now running!
echo Keep this window open to maintain the servers
echo.
pause
