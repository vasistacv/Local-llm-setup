"""
=============================================================
COLLEGE AI ENTERPRISE - KUBEFLOW STARTER (No-Root Edition)
=============================================================
Uses llama-cpp-python instead of Ollama.
No sudo needed. Works entirely as jovyan user.

Run: python start_kubeflow.py
=============================================================
"""
import os
import sys
import subprocess
import time
from pathlib import Path

HOME = Path.home()
WORK_DIR = HOME / "Local-llm-setup"
DATA_DIR = HOME / "ai_data"
MODELS_DIR = DATA_DIR / "models"

# Small but capable models for initial testing
# (Switch to 70b once system is confirmed working)
MODEL_GENERAL_REPO = "bartowski/Llama-3.2-3B-Instruct-GGUF"
MODEL_GENERAL_FILE = "Llama-3.2-3B-Instruct-Q4_K_M.gguf"

MODEL_CODING_REPO = "bartowski/Qwen2.5-Coder-3B-Instruct-GGUF"
MODEL_CODING_FILE = "Qwen2.5-Coder-3B-Instruct-Q4_K_M.gguf"

def banner(msg):
    print(f"\n{'='*55}\n  {msg}\n{'='*55}\n")

def run(cmd):
    print(f">> {cmd}")
    os.system(cmd)

def main():
    banner("COLLEGE AI - KUBEFLOW NO-ROOT DEPLOYMENT")

    # Step 1: Create directories
    banner("Step 1: Creating directories")
    for d in [MODELS_DIR, DATA_DIR/"memory", DATA_DIR/"logs"]:
        d.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Directories at {DATA_DIR}")

    # Step 2: Install packages
    banner("Step 2: Installing Python packages")
    run(f"{sys.executable} -m pip install -q llama-cpp-python huggingface_hub fastapi uvicorn requests loguru python-dotenv")
    print("[OK] Packages installed")

    # Step 3: Download models from HuggingFace
    banner("Step 3: Downloading AI Models from HuggingFace")
    try:
        from huggingface_hub import hf_hub_download
        
        print(f"\n>> Downloading General Model ({MODEL_GENERAL_FILE})...")
        general_path = hf_hub_download(
            repo_id=MODEL_GENERAL_REPO,
            filename=MODEL_GENERAL_FILE,
            local_dir=str(MODELS_DIR)
        )
        print(f"[OK] General model at: {general_path}")

        print(f"\n>> Downloading Coding Model ({MODEL_CODING_FILE})...")
        coding_path = hf_hub_download(
            repo_id=MODEL_CODING_REPO,
            filename=MODEL_CODING_FILE,
            local_dir=str(MODELS_DIR)
        )
        print(f"[OK] Coding model at: {coding_path}")

    except Exception as e:
        print(f"[ERROR] Model download failed: {e}")
        print("Check internet access or try: huggingface-cli login")
        return

    # Step 4: Write model paths to env file
    banner("Step 4: Saving configuration")
    env_content = f"""
LLAMA_MODEL_GENERAL={general_path}
LLAMA_MODEL_CODING={coding_path}
API_DB_PATH={DATA_DIR}/memory/api_keys.db
ADMIN_MASTER_KEY=sk-admin-college-ai-h200-master-999
"""
    env_path = WORK_DIR / "config" / "runtime.env"
    env_path.write_text(env_content)
    print(f"[OK] Config saved to {env_path}")

    # Step 5: Launch server
    banner("Step 5: Launching College AI Server")
    os.chdir(WORK_DIR)
    os.environ["LLAMA_MODEL_GENERAL"] = str(general_path)
    os.environ["LLAMA_MODEL_CODING"]  = str(coding_path)
    os.environ["API_DB_PATH"] = str(DATA_DIR / "memory" / "api_keys.db")
    
    print("[INFO] Starting server on http://0.0.0.0:8000")
    run(f"{sys.executable} server_llama.py")

if __name__ == "__main__":
    main()
