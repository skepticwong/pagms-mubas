@echo off
echo Testing PAGMS Login...
echo.

cd /d "%~dp0"

echo Current directory: %CD%
echo.

echo Testing Python...
python --version
echo.

echo Running login test...
python simple_test.py

echo.
pause
