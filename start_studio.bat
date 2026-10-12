@echo off
title POD Photorealistic Mockup Studio
cd /d "%~dp0"
echo ===================================================
echo     STARTING POD MOCKUP LIVE PREVIEW STUDIO
echo ===================================================
start http://127.0.0.1:5000
python app.py
pause
