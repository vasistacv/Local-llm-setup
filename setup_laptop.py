"""
[SAFE SETUP - LAPTOP MODE]
==========================
Uses LLama 3.2 (3B) and Qwen 2.5 (3B) for maximum efficiency.
Prevents system freezing and OOM errors.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# --- CONFIGURATION ---
BASE_DIR = Path(os.getcwd())
DATA_DIR = BASE_DIR / "data"

# Local Paths
CACHE_DIR = DATA_DIR / "cache"
TEMP_DIR = DATA_DIR / "tmp"
MODELS_DIR = DATA_DIR / "models"
OLLAMA_MODELS_DIR = MODELS_DIR / "ollama"

# Set Environment Variables
os.environ["PIP_CACHE_DIR"] = str(CACHE_DIR / "pip")
os.environ["HF_HOME"] = str(CACHE_DIR / "huggingface")
os.environ["OLLAMA_MODELS"] = str(OLLAMA_MODELS_DIR)
os.environ["TMP"] = str(TEMP_DIR)
os.environ["TEMP"] = str(TEMP_DIR)
os.environ["XDG_CACHE_HOME"] = str(CACHE_DIR)

# Local Ollama Path
OLLAMA_DIR = BASE_DIR / "ollama"
OLLAMA_EXE = OLLAMA_DIR / "ollama.exe"

# NEW SAFE MODELS (Less than 2GB each)
MODELS = [
    "llama3.2:3b",
    "qwen2.5-coder:3b"
]

def print_step(msg):
    print(f"\n[STEP] {msg}")
    print("=" * 50)
    time.sleep(1)

def ensure_directories():
    print_step("Creating Local Directories")
    for path in [DATA_DIR, CACHE_DIR, TEMP_DIR, MODELS_DIR, OLLAMA_MODELS_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    print(f"[OK] checked {DATA_DIR}")

def configure_ollama():
    print_step("Configuring Ollama")
    
    ollama_cmd = "ollama"
    if OLLAMA_EXE.exists():
        print(f"Using local file: {OLLAMA_EXE.name}")
        ollama_cmd = str(OLLAMA_EXE)
    else:
        print("[WARN] Using system ollama (if installed)")
    
    # Kill existing to be safe
    subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"], capture_output=True)
    
    return ollama_cmd

def pull_models_locally(ollama_cmd):
    print_step("Downloading Optimized Models (~2GB each)")
    print("These are small and fast. Should download quickly.")
    
    print("Starting background server...")
    with open(os.devnull, 'w') as devnull:
        server_process = subprocess.Popen(
            [ollama_cmd, "serve"], 
            env=os.environ,
            stdout=devnull,
            stderr=devnull,
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
    
    print("Waiting 5s for server...")
    time.sleep(5)
    
    success = True
    
    for model in MODELS:
        print(f"\n>> PROCESSING: {model}")
        try:
            # Check if exists
            subprocess.run([ollama_cmd, "pull", model], env=os.environ, check=True)
            print(f"[SUCCESS] {model} is installed.")
        except Exception as e:
            print(f"[ERROR] Failed {model}: {e}")
            success = False
            
    print("Cleanup: Stopping temp server...")
    server_process.terminate()
    try:
        server_process.wait(timeout=3)
    except:
        server_process.kill()
        
    subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"], capture_output=True)
    return success

def create_launch_scripts(python_exe):
    print_step("Creating Efficient Launch Scripts")
    
    bat_content = f"""@echo off
title College AI Enterprise (Laptop Mode)
echo Starting Optimized AI System...
echo ===================================================
echo [INFO] Interface available at: http://localhost:8000
echo ===================================================

:: 1. Force Local Paths
set "BASE_DIR={BASE_DIR}"
set "DATA_DIR=%BASE_DIR%\\data"
set "OLLAMA_MODELS=%DATA_DIR%\\models\\ollama"
set "HF_HOME=%DATA_DIR%\\cache\\huggingface"
set "PIP_CACHE_DIR=%DATA_DIR%\\cache\\pip"
set "TMP=%DATA_DIR%\\tmp"
set "TEMP=%DATA_DIR%\\tmp"

:: 2. Set Path for Local Ollama
set "PATH=%BASE_DIR%\\ollama;%PATH%"

:: 3. Initial Cleanup
taskkill /F /IM ollama.exe >nul 2>&1

:: 4. Start Ollama (Background)
echo [SYSTEM] Starting Engine...
start /B ollama serve >nul 2>&1

:: 5. Wait for Engine
timeout /t 3 /nobreak >nul

:: 6. Start Backend Server
"{python_exe}" server.py
pause
"""
    with open("START_COLLEGE_AI.bat", "w") as f:
        f.write(bat_content)
    
    print("[OK] Created START_COLLEGE_AI.bat")

def main():
    print("\n[COLLEGE AI - LAPTOP OPTIMIZED SETUP]\n")
    
    ensure_directories()
    
    venv_python = BASE_DIR / "nova_env" / "Scripts" / "python.exe"
    if not venv_python.exists():
        # Fallback to system python just for setup if venv missing
        venv_python = sys.executable

    ollama_cmd = configure_ollama()
    
    if pull_models_locally(ollama_cmd):
        create_launch_scripts(venv_python)
        print("\n[SETUP COMPLETE!]")
        print("Run 'START_COLLEGE_AI.bat' to start the system.")
    else:
        print("\n[SETUP FAILED]")

if __name__ == "__main__":
    main()
