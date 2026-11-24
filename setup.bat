@echo off
rem Create venv and install dependencies (needs Python 3.13 and internet)
cd /d "%~dp0"
if not exist venv (
  python -m venv venv
)
venv\Scripts\python.exe -m pip install -r requirements.txt
echo.
echo Done. Double-click run_dashboard.bat to start.
pause
