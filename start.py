#!/usr/bin/env python3
"""
=============================================================
COLLEGE AI ENTERPRISE - ONE-CLICK KUBEFLOW STARTER
=============================================================
Just run this ONE command from anywhere in the project:
    python start.py
=============================================================
"""
import os
import sys
import subprocess
import time
from pathlib import Path

# Auto-detect where this script lives (works anywhere on any OS)
WORK_DIR  = Path(__file__).parent.resolve()
DATA_DIR  = WORK_DIR / "data"
LOG_DIR   = DATA_DIR / "logs"
MEM_DIR   = DATA_DIR / "memory"

# H200 Models
MODEL_GENERAL = "llama3.1:70b"
MODEL_CODING  = "qwen2.5-coder:72b"

def banner(msg):
    print(f"\n{'='*55}\n  {msg}\n{'='*55}\n")

def run(cmd, check=False):
    print(f">> {cmd}")
    return subprocess.run(cmd, shell=True, check=check)

def ollama_running():
    r = subprocess.run("curl -s http://localhost:11434/api/tags", shell=True, capture_output=True)
    return r.returncode == 0

def main():
    banner("COLLEGE AI ENTERPRISE — H200 KUBEFLOW STARTUP")

    # ── Step 1: Directories ───────────────────────────────
    banner("Step 1: Creating directories")
    for d in [LOG_DIR, MEM_DIR, DATA_DIR/"tmp"]:
        d.mkdir(parents=True, exist_ok=True)
    print("[OK] Directories ready")

    # ── Step 2: Python packages ───────────────────────────
    banner("Step 2: Installing Python packages")
    run(f"{sys.executable} -m pip install fastapi uvicorn requests loguru python-dotenv -q", check=True)
    print("[OK] Packages installed")

    # ── Step 3: Check/Install Ollama ──────────────────────
    banner("Step 3: Checking Ollama")
    result = subprocess.run("which ollama", shell=True, capture_output=True)
    if result.returncode != 0:
        print("Ollama not found. Installing...")
        run("curl -fsSL https://ollama.com/install.sh | sh", check=True)
    else:
        print("[OK] Ollama already installed at:", result.stdout.decode().strip())

    # ── Step 4: Start Ollama if not running ───────────────
    banner("Step 4: Starting Ollama engine")
    if ollama_running():
        print("[OK] Ollama is already running!")
    else:
        print("Starting Ollama in background...")
        log = open(LOG_DIR / "ollama.log", "w")
        subprocess.Popen("ollama serve", shell=True, stdout=log, stderr=log)
        print("Waiting for Ollama to be ready...")
        for i in range(15):
            time.sleep(2)
            if ollama_running():
                print("[OK] Ollama is ready!")
                break
            print(f"  Waiting... ({(i+1)*2}s)")

    # ── Step 5: Pull models ───────────────────────────────
    banner("Step 5: Downloading AI Models")
    for model in [MODEL_GENERAL, MODEL_CODING]:
        print(f"\n>> Pulling {model} (this may take a while)...")
        run(f"ollama pull {model}")
        print(f"[OK] {model} ready!")

    # ── Step 6: Launch server ─────────────────────────────
    banner("Step 6: Launching College AI Server")
    os.chdir(WORK_DIR)
    print(f"[INFO] Working directory: {WORK_DIR}")
    print("[INFO] Server will start at: http://0.0.0.0:8000")
    print("[INFO] Admin Key: sk-admin-college-ai-h200-master-999")
    print("[INFO] Press Ctrl+C to stop\n")
    run(f"{sys.executable} server.py")

if __name__ == "__main__":
    main()
