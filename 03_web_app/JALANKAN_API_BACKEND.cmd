@echo off
cd /d "%~dp0"
wsl.exe -d Ubuntu-22.04 --exec /home/jonatomic/skripsi-batak-toba/.venv-web/bin/python "/mnt/d/SKRIPSIJONATHAN/PROGRAM/04_WEB_APP_BATAK_TOBA/jalankan_api.py"
pause
