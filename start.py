#!/usr/bin/env python3
"""
=============================================================
COLLEGE AI ENTERPRISE — ONE-CLICK KUBEFLOW STARTER
=============================================================
Run this ONE command from the project folder:
    python start.py

Does everything automatically:
  1. Creates required directories
  2. Installs Python packages
  3. Checks Ollama (installs if missing)
  4. Starts Ollama engine
  5. Downloads all 3 AI models
  6. Launches the server on port 8000
=============================================================
"""
import os
import sys
import subprocess
import time
from pathlib import Path

# ── Auto-detect project root (works on any machine/path) ──
WORK_DIR = Path(__file__).parent.resolve()
DATA_DIR = WORK_DIR / "data"
LOG_DIR  = DATA_DIR / "logs"
MEM_DIR  = DATA_DIR / "memory"

# ── 3 Advanced Models ──────────────────────────────────────
MODEL_GENERAL = "qwen2.5:14b"            # Best general model fitting in 15.4GB GPU
MODEL_CODING  = "qwen2.5-coder:14b"     # Best coding model fitting in 15.4GB GPU

def banner(msg):
    print(f"\n{'='*60}\n  {msg}\n{'='*60}\n")

def run(cmd):
    print(f">> {cmd}")
    subprocess.run(cmd, shell=True)

def ollama_running():
    r = subprocess.run(
        "curl -s http://localhost:11434/api/tags",
        shell=True, capture_output=True
    )
    return r.returncode == 0

def main():
    banner("COLLEGE AI ENTERPRISE — H200 KUBEFLOW STARTUP")
    print(f"  Project dir : {WORK_DIR}")
    print(f"  Models      : {MODEL_GENERAL} (General), {MODEL_CODING} (Coding)")

    # ── Step 1: Directories ───────────────────────────────
    banner("Step 1: Creating directories")
    for d in [LOG_DIR, MEM_DIR, DATA_DIR/"tmp"]:
        d.mkdir(parents=True, exist_ok=True)
    print("[OK] Directories ready")

    # ── Step 2: Python packages ───────────────────────────
    banner("Step 2: Installing Python packages")
    run(f"{sys.executable} -m pip install fastapi uvicorn requests loguru python-dotenv -q")
    print("[OK] Packages installed")

    # ── Step 3: Ollama check ──────────────────────────────
    banner("Step 3: Checking Ollama")
    result = subprocess.run("which ollama", shell=True, capture_output=True)
    if result.returncode != 0:
        print("Ollama not found. Installing now...")
        run("curl -fsSL https://ollama.com/install.sh | sh")
    else:
        print(f"[OK] Ollama found: {result.stdout.decode().strip()}")

    # ── Step 4: Start Ollama ──────────────────────────────
    banner("Step 4: Starting Ollama engine")
    if ollama_running():
        print("[OK] Ollama already running!")
    else:
        log = open(LOG_DIR / "ollama.log", "w")
        subprocess.Popen("ollama serve", shell=True, stdout=log, stderr=log)
        print("Waiting for Ollama to be ready...")
        for i in range(15):
            time.sleep(2)
            if ollama_running():
                print("[OK] Ollama is ready!")
                break
            print(f"  Waiting... ({(i+1)*2}s)")

    # ── Step 5: Pull all 3 models ─────────────────────────
    banner("Step 5: Downloading 3 AI Models")
    for model, desc in [
        (MODEL_GENERAL, "General Intelligence — 70B"),
        (MODEL_CODING,  "Coding Expert       — 32B"),
    ]:
        print(f"\n>> Pulling {model} ({desc})...")
        subprocess.run(f"ollama pull {model}", shell=True)
        print(f"[OK] {model} ready!")

    # ── Step 6: Launch server ─────────────────────────────
    banner("Step 6: Launching College AI Server")
    os.chdir(WORK_DIR)
    print(f"[INFO] Working dir : {WORK_DIR}")
    print(f"[INFO] Server URL  : http://0.0.0.0:8000")
    print(f"[INFO] Admin Key   : sk-admin-college-ai-h200-master-999")
    print(f"[INFO] Press Ctrl+C to stop\n")
    subprocess.run(f"{sys.executable} server.py", shell=True)

if __name__ == "__main__":
    main()
