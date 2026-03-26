@echo off
echo Starting PAGMS Backend Server...
echo.
echo Current directory: %CD%
echo.

cd /d "%~dp0backend"

echo Checking Python...
python --version
echo.

echo Starting Flask app...
echo You should see "Running on http://0.0.0.0:5000" below:
echo.

python app.py

echo.
echo Backend server stopped.
pause
