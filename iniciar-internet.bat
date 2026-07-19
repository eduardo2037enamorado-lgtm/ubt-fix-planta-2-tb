@echo off
title UBT Fix Planta 2 TB - Internet (datos moviles)
cd /d "%~dp0"

echo ==================================================
echo   UBT Fix - Planta 2 TB (acceso por internet)
echo ==================================================
echo   Iniciando servidor y tunel publico...
echo   Deja esta ventana abierta en la PC de planta.
echo   Codigo de acceso: 1010
echo ==================================================

start "UBT Fix Servidor" /min cmd /c "python iniciar_servidor.py"
timeout /t 3 /nobreak >nul
cloudflared tunnel --url http://127.0.0.1:5000
