"""
[SAFE SETUP - LOW RESOURCE MODE]
================================
Designed to be gentle on system memory (RAM/VRAM).
Sequential downloads with explicit pauses.
"""

import os
import sys
import subprocess
import time
import shutil
from pathlib import Path

# --- CONFIGURATION ---
BASE_DIR = Path(os.getcwd())
DATA_DIR = BASE_DIR / "data"

# FORCE CPU MODE FOR SETUP (Prevents VRAM OOM)
os.environ["OLLAMA_NUM_GPU"] = "0"
os.environ["CUDA_VISIBLE_DEVICES"] = ""

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

# Local Ollama Path
OLLAMA_DIR = BASE_DIR / "ollama"
OLLAMA_EXE = OLLAMA_DIR / "ollama.exe"

# Models (One by one)
MODELS = [
    "llama3.1:8b-instruct-q4_K_M",
    "qwen2.5-coder:7b"
]

def print_step(msg):
    print(f"\n[STEP] {msg}")
    print("=" * 50)
    time.sleep(1) # Pause for readability/system catch-up

def ensure_directories():
    print_step("Creating Directories")
    for path in [DATA_DIR, CACHE_DIR, TEMP_DIR, MODELS_DIR, OLLAMA_MODELS_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    print(f"[OK] checked {DATA_DIR}")

def configure_ollama():
    print_step("Configuring Ollama (CPU Mode for Download)")
    
    ollama_cmd = "ollama"
    if OLLAMA_EXE.exists():
        print(f"Using local Ollama: {OLLAMA_EXE.name}")
        ollama_cmd = str(OLLAMA_EXE)
    
    # Kill any rogue instances
    subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"], capture_output=True)
    time.sleep(2)
    
    return ollama_cmd

def safe_pull_models(ollama_cmd):
    print_step("Starting Safe Download Sequence")
    
    # Start server in background
    print("Starting background server...")
    with open(os.devnull, 'w') as devnull:
        # Prevent any output buffering
        server_process = subprocess.Popen(
            [ollama_cmd, "serve"], 
            env=os.environ,
            stdout=devnull,
            stderr=devnull,
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
    
    print("Waiting 10s for server to stabilize...")
    time.sleep(10)
    
    success = True
    
    for model in MODELS:
        print_step(f"Processing Model: {model}")
        print("This may take time. Please wait...")
        
        try:
            # Run pull command - Let it stream to stdout so user sees progress
            # Verify check logic
            ret = subprocess.call([ollama_cmd, "pull", model], env=os.environ)
            
            if ret == 0:
                print(f"[SUCCESS] {model} is ready.")
            else:
                print(f"[ERROR] Failed to download {model}. Code: {ret}")
                success = False
                
            # Free memory explicitly? Ollama manages this, but let's pause.
            print("Cooling down (5s)...")
            time.sleep(5)
            
        except Exception as e:
            print(f"[EXCEPTION] {e}")
            success = False

    print("Stopping setup server...")
    server_process.terminate()
    try:
        server_process.wait(timeout=5)
    except:
        server_process.kill()
        
    # Double check kill
    subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"], capture_output=True)
    return success

def create_launch_scripts(python_exe):
    print_step("Creating Launch Scripts")
    
    # Notice: We remove the CPU restriction for the actual launch script so it uses GPU later
    bat_content = f"""@echo off
title College AI Enterprise Server
echo Starting College AI System...
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

:: 3. GPU Enable (Default)
:: set "OLLAMA_NUM_GPU=1" 

:: 4. Initial Cleanup
taskkill /F /IM ollama.exe >nul 2>&1

:: 5. Start Ollama (Background)
echo [SYSTEM] Starting Local AI Engine...
start /B ollama serve >nul 2>&1

:: 6. Wait for Engine
timeout /t 5 /nobreak >nul

:: 7. Start Backend Server
"{python_exe}" server.py
pause
"""
    with open("START_COLLEGE_AI.bat", "w") as f:
        f.write(bat_content)
    
    print("[OK] Created START_COLLEGE_AI.bat")

def main():
    print("\n[COLLEGE AI - SAFE SETUP]\n")
    print("Running in Low-Memory Mode to prevent OOM errors.")
    
    ensure_directories()
    
    venv_python = BASE_DIR / "nova_env" / "Scripts" / "python.exe"
    if not venv_python.exists():
        print("[ERROR] Python environment missing. Please run 'python setup_college.py' first just for env setup.")
        # Try to use current python if venv missing?
        venv_python = sys.executable

    ollama_cmd = configure_ollama()
    
    if safe_pull_models(ollama_cmd):
        create_launch_scripts(venv_python)
        print("\n[SETUP COMPLETE]")
        print("You can now run START_COLLEGE_AI.bat")
    else:
        print("\n[SETUP FAILED]")
        print("Check internet connection or disk space.")

if __name__ == "__main__":
    main()
