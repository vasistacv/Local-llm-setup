"""
=============================================================
COLLEGE AI SERVER - llama-cpp-python Edition (No Ollama)
=============================================================
Works without Ollama. Uses llama-cpp-python directly.
GPU accelerated via CUDA automatically.
=============================================================
"""

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Generator
from loguru import logger
from pathlib import Path
import os

from core.auth import AuthManager

app = FastAPI(title="College AI Enterprise (llama-cpp)", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Config ─────────────────────────────────────────────────
ADMIN_KEY     = os.environ.get("ADMIN_MASTER_KEY", "sk-admin-college-ai-h200-master-999")
API_DB_PATH   = os.environ.get("API_DB_PATH", "data/memory/api_keys.db")
MODEL_GENERAL = os.environ.get("LLAMA_MODEL_GENERAL", "")
MODEL_CODING  = os.environ.get("LLAMA_MODEL_CODING",  "")

auth_manager = AuthManager(API_DB_PATH)

# ── Load LLM models ────────────────────────────────────────
logger.info("Loading AI models into GPU...")

try:
    from llama_cpp import Llama

    llm_general = Llama(
        model_path=MODEL_GENERAL,
        n_gpu_layers=-1,   # Use ALL GPU layers (H200 can handle everything)
        n_ctx=8192,
        verbose=False
    )
    logger.info(f"[OK] General model loaded: {Path(MODEL_GENERAL).name}")

    llm_coding = Llama(
        model_path=MODEL_CODING,
        n_gpu_layers=-1,
        n_ctx=8192,
        verbose=False
    )
    logger.info(f"[OK] Coding model loaded: {Path(MODEL_CODING).name}")

except Exception as e:
    logger.error(f"Model loading failed: {e}")
    llm_general = None
    llm_coding  = None

# ── Routing Logic ──────────────────────────────────────────
CODING_KEYWORDS = [
    "code", "python", "java", "javascript", "function", "class", "debug",
    "error", "bug", "program", "script", "algorithm", "sql", "html", "css",
    "c++", "typescript", "api", "json", "compile", "terminal"
]

def route_model(prompt: str):
    lower = prompt.lower()
    if any(kw in lower for kw in CODING_KEYWORDS):
        logger.info("Routed → CODING model")
        return llm_coding, "You are the world's best coding AI running on an H200 GPU. Write clean, correct, and efficient code."
    logger.info("Routed → GENERAL model")
    return llm_general, "You are an advanced enterprise AI running on an H200 GPU cluster. Provide detailed, accurate, and structured answers."

# ── Auth ───────────────────────────────────────────────────
def verify_api_key(request: Request):
    key = request.headers.get("x-api-key", "")
    if not key:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            key = auth_header.split(" ")[1]
    if not key:
        raise HTTPException(401, "Missing API Key.")
    if key == ADMIN_KEY:
        return "admin"
    if not auth_manager.validate_key(key):
        raise HTTPException(403, "Invalid or Revoked API Key.")
    return key

# ── Request Models ─────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str

class APIKeyRequest(BaseModel):
    owner_name: str
    admin_key: str

# ── Endpoints ──────────────────────────────────────────────
@app.post("/chat")
async def chat(req: ChatRequest, api_key: str = Depends(verify_api_key)):
    model, system_prompt = route_model(req.message)
    if model is None:
        raise HTTPException(500, "Models not loaded. Check server logs.")

    def stream() -> Generator:
        response = model.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": req.message}
            ],
            stream=True,
            max_tokens=4096,
            temperature=0.6
        )
        for chunk in response:
            delta = chunk["choices"][0]["delta"].get("content", "")
            if delta:
                yield delta

    return StreamingResponse(stream(), media_type="text/plain")

@app.post("/api/admin/keys/generate")
async def generate_key(req: APIKeyRequest):
    if req.admin_key != ADMIN_KEY:
        raise HTTPException(403, "Invalid Admin Key.")
    key = auth_manager.generate_api_key(req.owner_name)
    return {"status": "success", "owner": req.owner_name, "api_key": key}

@app.get("/api/admin/keys/list")
async def list_keys(admin_key: str):
    if admin_key != ADMIN_KEY:
        raise HTTPException(403, "Invalid Admin Key.")
    rows = auth_manager.list_keys()
    return {"keys": [{"id": r[0], "owner": r[1], "created": r[2], "active": r[3], "calls": r[4]} for r in rows]}

@app.get("/api/system/status")
async def status():
    return {
        "status": "online",
        "engine": "llama-cpp-python",
        "general_model": Path(MODEL_GENERAL).name if MODEL_GENERAL else "not loaded",
        "coding_model":  Path(MODEL_CODING).name  if MODEL_CODING  else "not loaded",
        "gpu": "H200 CUDA"
    }

app.mount("/", StaticFiles(directory="ui", html=True), name="ui")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting College AI on 0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
