@echo off
title Vibe Coder
echo Starting Vibe Coder on port 8502...
echo.
echo Make sure Ollama is running (ollama serve)
echo.
cd /d "%~dp0"
streamlit run app.py --server.port 8502 --server.headless false
pause
