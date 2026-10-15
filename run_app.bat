@echo off
REM PoultryGuard PoC launcher (Windows)
cd /d "%~dp0"
echo Starting PoultryGuard AI ...
streamlit run app.py
pause
