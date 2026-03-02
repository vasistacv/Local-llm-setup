@echo off
title College AI Enterprise (Laptop Mode)
echo Starting Optimized AI System...
echo ===================================================
echo [INFO] Interface available at: http://localhost:8000
echo ===================================================

:: 1. Force Local Paths
set "BASE_DIR=D:\AI_ASSISTANT"
set "DATA_DIR=%BASE_DIR%\data"
set "OLLAMA_MODELS=%DATA_DIR%\models\ollama"
set "HF_HOME=%DATA_DIR%\cache\huggingface"
set "PIP_CACHE_DIR=%DATA_DIR%\cache\pip"
set "TMP=%DATA_DIR%\tmp"
set "TEMP=%DATA_DIR%\tmp"

:: 2. Set Path for Local Ollama
set "PATH=%BASE_DIR%\ollama;%PATH%"

:: 3. Initial Cleanup
taskkill /F /IM ollama.exe >nul 2>&1

:: 4. Start Ollama (Background)
echo [SYSTEM] Starting Engine...
start /B ollama serve >nul 2>&1

:: 5. Wait for Engine
timeout /t 3 /nobreak >nul

:: 6. Start Backend Server
"D:\AI_ASSISTANT\nova_env\Scripts\python.exe" server.py
pause
