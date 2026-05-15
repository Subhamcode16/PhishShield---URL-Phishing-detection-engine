@echo off
set "PYTHON_EXE=C:\Python313\python.exe"
set "PROJECT_DIR=%~dp0"

echo ===========================================
echo   🛡️  PhishShield AI - Security Launcher
echo ===========================================
echo.

:: 1. Force kill ANY existing python processes to be safe
echo 🧹 Performing Deep System Clean...
taskkill /f /im python.exe >nul 2>&1
powershell -Command "Get-NetTCPConnection -LocalPort 8000,8001,8002,3000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"
timeout /t 2 /nobreak > nul

:: 2. Verify Python Path
if not exist "%PYTHON_EXE%" (
    echo ❌ Error: Python not found at %PYTHON_EXE%
    pause
    exit /b
)

:: 3. Ensure we are in the right directory
cd /d "%PROJECT_DIR%"

echo 🚀 Launching ML Engine (Port 8002)...
start "PhishShield-API" cmd /k "cd /d "%PROJECT_DIR%" && "%PYTHON_EXE%" src/api/main.py"

echo ⏳ Waiting for model to load (10 seconds)...
timeout /t 10 /nobreak > nul

echo 🌐 Launching Dashboard (Port 3000)...
start "PhishShield-Frontend" cmd /k "cd /d "%PROJECT_DIR%" && "%PYTHON_EXE%" -m http.server 3000 --directory frontend"

echo 🔍 Opening browser...
timeout /t 2 /nobreak > nul
start http://127.0.0.1:3000

echo.
echo ===========================================
echo ✅  System is ONLINE on Port 8002.
echo ===========================================
echo.
pause
