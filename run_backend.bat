@echo off
cd /d "%~dp0backend"
echo Starting backend...
python app.py > backend_output.txt 2>&1
echo Backend output saved to backend_output.txt
type backend_output.txt
pause
