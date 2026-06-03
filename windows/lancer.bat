@echo off
title BlueBot — App Blocker
color 0B
echo.
echo  ==========================================
echo   BlueBot — App Blocker
echo   FIRST Tech Challenge Reims
echo  ==========================================
echo.

:: Verifier que Python est installe
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERREUR : Python n'est pas installe !
    echo.
    echo  Telecharge Python ici :
    echo  https://www.python.org/downloads/
    echo  (Coche bien "Add to PATH" lors de l'installation)
    echo.
    pause
    exit
)

echo  Installation des dependances...
pip install customtkinter psutil pillow -q --disable-pip-version-check

echo  Lancement de BlueBot...
echo.

cd /d "%~dp0"
python bluebot.py

pause
