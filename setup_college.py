"""
[COLLEGE AI ENTERPRISE SETUP SCRIPT]
=====================================
Automated setup for the offline AI Assistant.
ENSURES EVERYTHING IS LOCAL TO THIS FOLDER (D: DRIVE).
NO C: DRIVE ACCESS.
"""

import os
import sys
import subprocess
import shutil
import time
from pathlib import Path

# --- CONFIGURATION ---
BASE_DIR = Path(os.getcwd())
DATA_DIR = BASE_DIR / "data"

# 1. DEFINE LOCAL PATHS (The "Neat" Structure)
CACHE_DIR = DATA_DIR / "cache"
TEMP_DIR = DATA_DIR / "tmp"
MODELS_DIR = DATA_DIR / "models"
OLLAMA_MODELS_DIR = MODELS_DIR / "ollama"

# 2. OVERRIDE ENVIRONMENT VARIABLES (The "Safety" Lock)
# This forces all tools to use D: drive
os.environ["PIP_CACHE_DIR"] = str(CACHE_DIR / "pip")
os.environ["HF_HOME"] = str(CACHE_DIR / "huggingface")
os.environ["OLLAMA_MODELS"] = str(OLLAMA_MODELS_DIR)
os.environ["TMP"] = str(TEMP_DIR)
os.environ["TEMP"] = str(TEMP_DIR)
os.environ["XDG_CACHE_HOME"] = str(CACHE_DIR)

# Local Ollama Path
OLLAMA_DIR = BASE_DIR / "ollama"
OLLAMA_EXE = OLLAMA_DIR / "ollama.exe"

# Add local Ollama to PATH
if OLLAMA_DIR.exists():
    os.environ["PATH"] = str(OLLAMA_DIR) + os.pathsep + os.environ["PATH"]

# Models to Install
MODELS = [
    "llama3.1:8b-instruct-q4_K_M",  # General
    "qwen2.5-coder:7b"             # Coding
]

REQUIRED_PACKAGES = [
    "fastapi",
    "uvicorn",
    "requests",
    "loguru",
    "python-dotenv"
]

def print_step(msg):
    print(f"\n[STEP] {msg}")
    print("=" * 50)

def ensure_directories():
    print_step("Creating Local Directories")
    for path in [DATA_DIR, CACHE_DIR, TEMP_DIR, MODELS_DIR, OLLAMA_MODELS_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    print(f"[OK] All data folders created in {DATA_DIR}")
    print(f"[SAFE] Caches redirected to {CACHE_DIR}")

def setup_venv():
    print_step("Setting up Local Python Environment")
    venv_dir = BASE_DIR / "nova_env"
    
    if not venv_dir.exists():
        print("Creating virtual environment...")
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])
    
    # Return path to python executable in venv
    if os.name == 'nt':
        return venv_dir / "Scripts" / "python.exe"
    else:
        return venv_dir / "bin" / "python"

def install_packages(python_exe):
    print_step("Installing Packages Locally")
    print(f"Using Python: {python_exe}")
    
    # Check if packages installed
    try:
        # We use strict quiet installation to avoid clutter
        subprocess.check_call([str(python_exe), "-m", "pip", "install", "--quiet", "--upgrade", "pip"])
        subprocess.check_call([str(python_exe), "-m", "pip", "install", "--quiet"] + REQUIRED_PACKAGES)
        print("[OK] Packages installed locally.")
    except Exception as e:
        print(f"[ERROR] Failed to install packages: {e}")

def configure_ollama():
    print_step("Configuring Ollama (Local Models)")
    
    ollama_cmd = "ollama"
    if OLLAMA_EXE.exists():
        print(f"Using local Ollama at: {OLLAMA_EXE}")
        ollama_cmd = str(OLLAMA_EXE)
    else:
        print("[WARN] Local Ollama not found. Using system 'ollama' if available.")
    
    # Stop running instances
    subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"], capture_output=True)
    
    print(f"Setting OLLAMA_MODELS to: {OLLAMA_MODELS_DIR}")
    
    return True, ollama_cmd

def pull_models_locally(ollama_cmd):
    print_step("Downloading AI Models (To D: Drive)")
    
    print("Starting local Ollama server...")
    
    env = os.environ.copy()
    
    # Start server
    server_process = subprocess.Popen(
        [ollama_cmd, "serve"], 
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
    )
    
    print("Waiting for server to start...")
    time.sleep(5)
    
    for model in MODELS:
        print(f"\n>> Checking model: {model}")
        try:
            print(f"[DOWNLOADING] {model}...")
            # We use check=True to ensure we wait for it
            subprocess.run([ollama_cmd, "pull", model], env=env, check=True)
            print(f"[OK] {model} ready.")
        except Exception as e:
            print(f"[ERROR] Failed to handle model {model}: {e}")
            print("Please check internet connection.")
    
    print("Stopping temporary Setup Ollama server...")
    subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"], capture_output=True)

def create_launch_scripts(python_exe):
    print_step("Creating Launch Scripts")
    
    bat_content = f"""@echo off
title College AI Enterprise Server
echo Starting College AI System...
echo ===================================================
echo [INFO] Interface available at: http://localhost:8000
echo ===================================================

:: 1. Force Local Paths (Safety Lock)
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
echo [SYSTEM] Starting Local AI Engine...
start /B ollama serve >nul 2>&1

:: 5. Wait for Engine
timeout /t 5 /nobreak >nul

:: 6. Start Backend Server
"{python_exe}" server.py
pause
"""
    with open("START_COLLEGE_AI.bat", "w") as f:
        f.write(bat_content)
    
    print("[OK] Created START_COLLEGE_AI.bat")

def main():
    print("\n[COLLEGE AI ENTERPRISE SETUP - STRICT LOCAL MODE]\n")
    
    ensure_directories()
    
    python_exe = setup_venv()
    install_packages(python_exe)
    
    success, ollama_cmd = configure_ollama()
    if success:
        pull_models_locally(ollama_cmd)
    
    create_launch_scripts(python_exe)
    
    print("\n[SETUP COMPLETE!]")
    print("Run 'START_COLLEGE_AI.bat' to start the system.")

if __name__ == "__main__":
    main()
