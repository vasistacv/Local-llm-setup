"""
=============================================================
COLLEGE AI ENTERPRISE - HuggingFace Transformers Server
=============================================================
No Ollama needed. Uses HuggingFace Transformers + PyTorch.
GPU accelerated via CUDA. 4-bit quantization for efficiency.

Start: python server_hf.py
=============================================================
"""

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Generator
from pathlib import Path
from threading import Thread
from loguru import logger
import os
import torch

from core.auth import AuthManager

app = FastAPI(title="College AI Enterprise (HF Transformers)", version="4.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ADMIN_KEY   = os.environ.get("ADMIN_MASTER_KEY", "sk-admin-college-ai-h200-master-999")
API_DB_PATH = os.environ.get("API_DB_PATH", "data/memory/api_keys.db")

# Open-access models (no HuggingFace token required)
MODEL_GENERAL = os.environ.get("HF_MODEL_GENERAL", "Qwen/Qwen2.5-7B-Instruct")
MODEL_CODING  = os.environ.get("HF_MODEL_CODING",  "Qwen/Qwen2.5-Coder-7B-Instruct")

# Use 4-bit quantization for efficient GPU usage
USE_4BIT = os.environ.get("USE_4BIT", "true").lower() == "true"

auth_manager = AuthManager(API_DB_PATH)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOAD MODELS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
logger.info("Loading AI models... This may take a few minutes on first run.")

from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer, BitsAndBytesConfig

def load_model(model_id: str):
    """Load a model with 4-bit quantization for GPU efficiency."""
    logger.info(f"Loading {model_id}...")
    
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    
    if USE_4BIT and torch.cuda.is_available():
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True
        )
        logger.info(f"[OK] {model_id} loaded in 4-bit on GPU")
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        logger.info(f"[OK] {model_id} loaded in fp16")
    
    return model, tokenizer

try:
    general_model, general_tokenizer = load_model(MODEL_GENERAL)
    coding_model,  coding_tokenizer  = load_model(MODEL_CODING)
    logger.info("✅ All models loaded and ready!")
except Exception as e:
    logger.error(f"Model loading failed: {e}")
    general_model = coding_model = None
    general_tokenizer = coding_tokenizer = None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ROUTING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CODING_KEYWORDS = [
    "code", "python", "java", "javascript", "function", "class", "debug",
    "error", "bug", "program", "script", "algorithm", "sql", "html", "css",
    "c++", "typescript", "api", "json", "compile", "syntax", "terminal"
]

def route(prompt: str):
    lower = prompt.lower()
    if any(kw in lower for kw in CODING_KEYWORDS):
        logger.info("→ CODING model")
        return (
            coding_model, coding_tokenizer,
            "You are the world's best coding AI on an H200 GPU. Write clean, accurate, efficient code."
        )
    logger.info("→ GENERAL model")
    return (
        general_model, general_tokenizer,
        "You are an elite enterprise AI on an H200 GPU supercluster. Provide deep, accurate, structured answers."
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUTH
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def verify_api_key(request: Request):
    key = request.headers.get("x-api-key", "")
    if not key:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            key = auth.split(" ")[1]
    if not key:
        raise HTTPException(401, "Missing API Key.")
    if key == ADMIN_KEY:
        return "admin"
    if not auth_manager.validate_key(key):
        raise HTTPException(403, "Invalid or Revoked API Key.")
    return key

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REQUEST MODELS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ChatRequest(BaseModel):
    message: str

class APIKeyRequest(BaseModel):
    owner_name: str
    admin_key: str

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENDPOINTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.post("/chat")
async def chat(req: ChatRequest, api_key: str = Depends(verify_api_key)):
    if general_model is None:
        raise HTTPException(500, "Models not loaded. Check server logs.")
    
    model, tokenizer, system_prompt = route(req.message)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": req.message}
    ]
    
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text], return_tensors="pt").to(model.device)
    
    streamer = TextIteratorStreamer(tokenizer, skip_special_tokens=True, skip_prompt=True)
    
    gen_kwargs = dict(
        **inputs,
        streamer=streamer,
        max_new_tokens=4096,
        temperature=0.6,
        do_sample=True
    )
    
    thread = Thread(target=model.generate, kwargs=gen_kwargs)
    thread.start()
    
    def stream_response():
        for chunk in streamer:
            yield chunk
    
    return StreamingResponse(stream_response(), media_type="text/plain")

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
    return {"keys": [{"id":r[0],"owner":r[1],"created":r[2],"active":r[3],"calls":r[4]} for r in rows]}

@app.get("/api/system/status")
async def status():
    return {
        "status": "online",
        "engine": "HuggingFace Transformers + PyTorch",
        "cuda": torch.cuda.is_available(),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        "general_model": MODEL_GENERAL,
        "coding_model": MODEL_CODING
    }

app.mount("/", StaticFiles(directory="ui", html=True), name="ui")

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 College AI Enterprise — Starting on 0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
