@echo off
title SGHL - Demarrage local
echo.
echo ========================================
echo   SGHL - Systeme Hospitalier Local
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Preparation de la base demo...
python manage.py seed_sghl_demo
if errorlevel 1 (
    echo ERREUR: impossible d executer seed_sghl_demo
    echo Verifiez que Python est installe: python --version
    pause
    exit /b 1
)

echo.
echo [2/3] Demarrage du backend Django (port 8000)...
start "SGHL Backend" cmd /k "cd /d %~dp0 && python manage.py runserver 127.0.0.1:8000"

echo.
echo [3/3] Demarrage du frontend Vue (port 5174)...
start "SGHL Frontend" cmd /k "cd /d %~dp0sghl_frontend && npm run dev"

echo.
echo ========================================
echo   APPLICATION PRETE
echo ========================================
echo.
echo  Ouvrez votre navigateur sur:
echo    http://127.0.0.1:5174
echo.
echo  Compte demo docteur:
echo    Email     : doctor@sghl.com
echo    Password  : demo1234
echo    Role      : DOCTOR
echo    Service   : PED
echo.
echo  API backend:
echo    http://127.0.0.1:8000/api/v2/docs
echo.
pause
