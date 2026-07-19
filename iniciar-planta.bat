@echo off
title UBT Fix Planta 2 TB
cd /d "%~dp0"

echo.
echo Instalando dependencias si hace falta...
python -m pip install -r requirements.txt -q

echo.
python iniciar_servidor.py

pause
