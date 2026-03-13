@echo off
echo ==================================================
echo   CLINICA HD - SERVER LAUNCHER
echo ==================================================
echo.

echo [1/3] Closing any existing server instances...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo [2/3] Cleaning up Python processes...
taskkill /F /IM python.exe >nul 2>&1

echo [3/3] Starting FastAPI Server...
echo.
echo   - Server URL: http://127.0.0.1:8000/recepcion
echo   - Admin URL:  http://127.0.0.1:8000/admin
echo.
echo Press Ctrl+C to stop the server.
echo.

cd /d c:\HD\fastapi_project
python -m uvicorn main:app --reload --port 8000
pause
