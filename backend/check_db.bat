@echo off
cd /d "%~dp0instance"
echo Checking grants table structure...
sqlite3 pagms.db "PRAGMA table_info(grants);"
echo.
echo Checking sample grant data...
sqlite3 pagms.db "SELECT title, start_date, end_date FROM grants LIMIT 3;"
pause
