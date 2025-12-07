@echo off
REM FT-Echo Test Script for Windows
REM Runs the TCP server, performs test operations, and logs outputs

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set SERVER_DIR=%PROJECT_ROOT%\server
set DEMO_DATA_DIR=%PROJECT_ROOT%\demo_data
set STORAGE_DIR=%PROJECT_ROOT%\storage
set LOG_DIR=%SERVER_DIR%\logs
set TRANSCRIPT=%PROJECT_ROOT%\transcript.txt

REM Create necessary directories
if not exist "%DEMO_DATA_DIR%" mkdir "%DEMO_DATA_DIR%"
if not exist "%STORAGE_DIR%" mkdir "%STORAGE_DIR%"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo ========================================= > "%TRANSCRIPT%"
echo FT-Echo Test Run - %date% %time% >> "%TRANSCRIPT%"
echo ========================================= >> "%TRANSCRIPT%"
echo. >> "%TRANSCRIPT%"

echo Starting FT-Echo Test Suite
echo.

REM Create test files
echo Creating test files...
echo This is a small test file for FT-Echo protocol. > "%DEMO_DATA_DIR%\small.txt"
echo Line 1 >> "%DEMO_DATA_DIR%\small.txt"
echo Line 2 >> "%DEMO_DATA_DIR%\small.txt"
echo Line 3 >> "%DEMO_DATA_DIR%\small.txt"

REM Create a larger file for resume testing (using Python)
python -c "import os; f=open(r'%DEMO_DATA_DIR%\large.bin','wb'); f.write(os.urandom(102400)); f.close()" 2>nul

echo Test files created
echo.

REM Start TCP server in background
echo Starting TCP server on port 9000...
cd /d "%SERVER_DIR%"
start /B python tcp_server.py 9000 > "%LOG_DIR%\server_output.log" 2>&1
timeout /t 2 /nobreak >nul

echo Server started
echo.

REM Test 1: PUT operation
echo === TEST 1: PUT Operation ===
echo Uploading small.txt...
cd /d "%PROJECT_ROOT%"
python -c "from server.tcp_client_lib import put_file; import sys; result = put_file('localhost', 9000, 'demo_data/small.txt'); print('PUT Result:', result); print('SHA256:', result['sha']); print('Size:', result['size'], 'bytes')" 2>&1 | tee -a "%TRANSCRIPT%"
echo. >> "%TRANSCRIPT%"

REM Test 2: LIST operation
echo === TEST 2: LIST Operation ===
python -c "from server.tcp_client_lib import list_files; files = list_files('localhost', 9000); print('Found', len(files), 'files:'); [print('  -', f['name'], ':', f['size'], 'bytes') for f in files]" 2>&1 | tee -a "%TRANSCRIPT%"
echo. >> "%TRANSCRIPT%"

REM Test 3: GET operation
echo === TEST 3: GET Operation ===
echo Downloading small.txt...
python -c "from server.tcp_client_lib import get_file; import os; dest = 'storage/downloaded_small.txt'; os.remove(dest) if os.path.exists(dest) else None; result = get_file('localhost', 9000, 'small.txt', dest); print('GET Result:', result); print('SHA256:', result['sha']); print('Size:', result['size'], 'bytes')" 2>&1 | tee -a "%TRANSCRIPT%"
echo. >> "%TRANSCRIPT%"

REM Cleanup - stop server
echo Stopping server...
taskkill /F /FI "WINDOWTITLE eq *tcp_server*" >nul 2>&1
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *tcp_server*" >nul 2>&1

echo.
echo === Test Summary ===
echo All tests completed. Check transcript.txt for full output.
echo.
echo ========================================= >> "%TRANSCRIPT%"
echo Test Run Complete - %date% %time% >> "%TRANSCRIPT%"
echo ========================================= >> "%TRANSCRIPT%"

echo.
echo Test transcript saved to: %TRANSCRIPT%

pause

