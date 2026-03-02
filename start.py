#!/usr/bin/env python3
"""
=============================================================
COLLEGE AI ENTERPRISE - KUBEFLOW ONE-CLICK STARTER
=============================================================
Run this after git clone on the Kubeflow server terminal:
    python start.py
=============================================================
"""
import os
import sys
import subprocess
import time
from pathlib import Path

HOME = Path.home()
WORK_DIR = HOME / "AI_ASSISTANT"
DATA_DIR = WORK_DIR / "data"
MODELS_DIR = DATA_DIR / "models" / "ollama"

# Models to use (H200 can handle 70B easily)
MODEL_GENERAL = "llama3.1:70b"
MODEL_CODING  = "qwen2.5-coder:72b"

def run(cmd, **kwargs):
    print(f"\n>> {cmd}")
    return subprocess.run(cmd, shell=True, **kwargs)

def banner(msg):
    print(f"\n{'='*55}\n  {msg}\n{'='*55}")

def main():
    banner("COLLEGE AI ENTERPRISE - KUBEFLOW STARTUP")

    # 1. Create directories
    banner("Step 1: Creating directories")
    for d in [MODELS_DIR, DATA_DIR/"cache", DATA_DIR/"memory", DATA_DIR/"logs", DATA_DIR/"tmp"]:
        d.mkdir(parents=True, exist_ok=True)
    print("[OK] Directories ready")

    # 2. Set environment
    banner("Step 2: Setting environment")
    os.environ["OLLAMA_MODELS"] = str(MODELS_DIR)
    os.environ["OLLAMA_KEEP_ALIVE"] = "-1"
    os.environ["TMPDIR"] = str(DATA_DIR / "tmp")
    print(f"[OK] OLLAMA_MODELS = {MODELS_DIR}")

    # 3. Install Python packages
    banner("Step 3: Installing Python packages")
    run(f"{sys.executable} -m pip install -r {WORK_DIR}/requirements.txt -q")
    print("[OK] Packages installed")

    # 4. Install Ollama if not present
    banner("Step 4: Checking Ollama")
    result = subprocess.run("which ollama", shell=True, capture_output=True)
    if result.returncode != 0:
        print("Ollama not found. Installing...")
        run("curl -fsSL https://ollama.com/install.sh | sh")
    else:
        print(f"[OK] Ollama already installed")

    # 5. Start Ollama server
    banner("Step 5: Starting Ollama engine")
    subprocess.Popen(
        "ollama serve",
        shell=True,
        env=os.environ,
        stdout=open(DATA_DIR/"logs"/"ollama.log", "w"),
        stderr=subprocess.STDOUT
    )
    print("[OK] Ollama starting... waiting 8s")
    time.sleep(8)

    # 6. Pull models
    banner("Step 6: Downloading AI Models")
    for model in [MODEL_GENERAL, MODEL_CODING]:
        print(f"\n>> Pulling {model}...")
        run(f"ollama pull {model}")
        print(f"[OK] {model} ready")

    # 7. Launch server
    banner("Launching College AI Server on port 8000")
    os.chdir(WORK_DIR)
    print("[INFO] Server starting at http://localhost:8000")
    print("[INFO] Use Ctrl+C to stop\n")
    run(f"{sys.executable} server.py")

if __name__ == "__main__":
    main()
