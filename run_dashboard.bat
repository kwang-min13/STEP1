@echo off
echo Starting Local-Helix Dashboard...
echo.
echo Dashboard will open at: http://localhost:8501
echo Press Ctrl+C to stop the server
echo.

cd /d "%~dp0"
python -m streamlit run app.py
