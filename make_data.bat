@echo off
rem Regenerate the simulated orders and clean them (fixed random seed, reproducible)
cd /d "%~dp0"
venv\Scripts\python.exe src\generate_data.py
venv\Scripts\python.exe src\preprocess.py
pause
