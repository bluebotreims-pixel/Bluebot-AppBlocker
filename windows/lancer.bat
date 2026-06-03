@echo off
title BlueBot — App Blocker
color 0B
echo.
echo  ==========================================
echo   BlueBot — App Blocker
echo   Et oui mon garçon
echo  ==========================================
echo.

@echo off
title BlueBot App Blocker
chcp 65001 >nul
echo.
echo  BlueBot - App Blocker
echo.

cd /d "%~dp0"

echo  Installation des dependances...
py -m pip install customtkinter psutil pillow -q --disable-pip-version-check 2>nul
if errorlevel 1 (
    python -m pip install customtkinter psutil pillow -q --disable-pip-version-check 2>nul
)

echo  Lancement...
echo.

py bluebot.py 2>nul
if errorlevel 1 (
    python bluebot.py
)

pause
