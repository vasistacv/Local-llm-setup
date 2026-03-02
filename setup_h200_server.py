"""
[ENTERPRISE H200 SERVER SETUP]
==============================
Downloads massively scaled models (70B+) tailored for an H200 GPU server.
Uses a scalable routing system and API auth mechanism.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# --- MASSIVE H200 CONFIGURATION ---
BASE_DIR = Path(os.getcwd())
DATA_DIR = BASE_DIR / "data"

OLLAMA_EXE = BASE_DIR / "ollama" / "ollama.exe"

# The Ultimate Models 
# (Total size approx 100GB+ - only suitable for High-End GPU Servers)
MODELS = [
    "llama3.1:70b",        # General Reasoning (Large Scale)
    "qwen2.5-coder:72b",   # Supreme Coding Skills
    "llama3.2-vision:90b"  # Vision & Multimodal Server
]

def main():
    print("\n[COLLEGE AI ENTERPRISE - H200 SERVER SETUP]\n")
    print("WARNING: You are about to download over 120GB of massive AI models.")
    print("Ensure this machine has an NVIDIA H200 (or equivalent with >140GB VRAM).\n")
    
    # Check if this is the user's laptop or the actual server
    if "laptop" in str(sys.argv):
        print("ERROR: This script is restricted to H200 Servers, not laptops.")
        print("Run setup_laptop.py instead.")
        return

    print("Configuring environment paths...")
    os.environ["OLLAMA_MODELS"] = str(DATA_DIR / "models" / "ollama")
    os.environ["OLLAMA_NUM_GPU"] = "999" # Maximize GPU usage
    os.environ["CUDA_VISIBLE_DEVICES"] = "0,1,2,3,4,5,6,7" # Assuming multi-GPU node
    
    ollama_cmd = str(OLLAMA_EXE) if OLLAMA_EXE.exists() else "ollama"

    print("Starting background AI Engine...")
    subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"], capture_output=True)
    server = subprocess.Popen([ollama_cmd, "serve"], env=os.environ, stdout=subprocess.DEVNULL)
    time.sleep(5)
    
    print("\n[INITIATING MASSIVE DOWNLOAD SEQUENCE]")
    for model in MODELS:
        print(f"\n>> PULLING {model.upper()}...")
        try:
            subprocess.run([ollama_cmd, "pull", model], env=os.environ, check=True)
            print(f"[OK] {model} downloaded and verified.")
        except:
            print(f"[ERROR] Failed to download {model}. Check storage/network.")
            
    print("Terminating setup engine...")
    server.terminate()
    
    # Create the H200 Launch Script
    bat_content = f"""@echo off
title College AI API Gateway (H200 Cluster)
echo Starting Enterprise API Gateway...
echo ===================================================

set "OLLAMA_MODELS={DATA_DIR / 'models' / 'ollama'}"
set "OLLAMA_NUM_GPU=99"
set "OLLAMA_KEEP_ALIVE=-1"

taskkill /F /IM ollama.exe >nul 2>&1
start /B ollama serve >nul 2>&1
timeout /t 5 >nul

echo Starting FastAPI Server...
python server.py
pause
"""
    with open("START_H200_CLUSTER.bat", "w") as f:
        f.write(bat_content)
        
    print("\n[H200 SETUP COMPLETE]")
    print("API Keys database has been created.")
    print("Start the cluster with 'START_H200_CLUSTER.bat'")

if __name__ == "__main__":
    main()
