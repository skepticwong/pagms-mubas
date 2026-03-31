@echo off
echo 🚀 Starting PAGMS Asset Management Backend...
echo.
echo 📊 This will start the Flask server with all Phase 1-3 features:
echo    • Asset Management (Phase 1)
echo    • Rules Engine & Workflows (Phase 2)  
echo    • Advanced Analytics & Reporting (Phase 3)
echo.
echo 🌐 Server will start on: http://localhost:5000
echo 🔗 Health check: http://localhost:5000/health
echo.
echo Press Ctrl+C to stop the server
echo ================================
echo.

python start_app.py

pause
