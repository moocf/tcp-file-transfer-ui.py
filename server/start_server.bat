@echo off
REM Windows batch file to start the TCP server
REM Usage: start_server.bat [port]

set PORT=%1
if "%PORT%"=="" set PORT=9000

echo Starting FT-Echo TCP Server on port %PORT%...
python tcp_server.py %PORT%

