@echo off
rem Start the dashboard (http://localhost:8501)
cd /d "%~dp0"
if exist venv\Scripts\streamlit.exe (
  venv\Scripts\streamlit.exe run src\app.py --server.port 8501
) else (
  echo venv not found, using system streamlit. Run setup.bat first if this fails.
  streamlit run src\app.py --server.port 8501
)
pause
