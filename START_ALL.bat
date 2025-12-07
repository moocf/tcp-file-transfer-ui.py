@echo off
REM Complete startup script for FT-Echo project
REM Starts TCP server, FastAPI, and React frontend

echo ========================================
echo FT-Echo Project Startup Script
echo ========================================
echo.

set PROJECT_ROOT=%~dp0
set SERVER_DIR=%PROJECT_ROOT%server
set FRONTEND_DIR=%PROJECT_ROOT%frontend

echo Step 1: Starting TCP Server...
start "FT-Echo TCP Server" cmd /k "cd /d %SERVER_DIR% && python tcp_server.py 9000"
timeout /t 3 /nobreak >nul

echo Step 2: Starting FastAPI Server...
start "FT-Echo FastAPI" cmd /k "cd /d %SERVER_DIR% && python fastapi_app.py"
timeout /t 3 /nobreak >nul

echo Step 3: Starting React Frontend...
start "FT-Echo React" cmd /k "cd /d %FRONTEND_DIR% && npm start"

echo.
echo ========================================
echo All servers starting...
echo ========================================
echo.
echo TCP Server:    http://localhost:9000 (direct TCP)
echo FastAPI:       http://localhost:8000 (HTTP API)
echo React App:     http://localhost:3000 (will open automatically)
echo.
echo Keep all windows open!
echo.
echo Press any key to exit this window (servers will keep running)...
pause >nul

