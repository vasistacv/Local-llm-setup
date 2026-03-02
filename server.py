"""
🌐 Enterprise API Gateway (H200 Server Edition)
================================================
FastAPI backend that handles API Key authentication, 
routing, and exposing the massive AI cluster to external clients.
"""

from fastapi import FastAPI, HTTPException, Request, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from loguru import logger
import os

from core.auth import AuthManager
from brain.college_brain import CollegeBrain
from config.config import settings

app = FastAPI(title="College AI (H200 Enterprise API)", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Core Services
brain = CollegeBrain()

# Initialize API Auth
API_DB_PATH = os.environ.get("API_DB_PATH", "data/memory/api_keys.db")
auth_manager = AuthManager(API_DB_PATH)
ADMIN_KEY = os.environ.get("ADMIN_MASTER_KEY", "sk-admin-college-ai-h200-master-999")

# --- DATA MODELS ---
class ChatRequest(BaseModel):
    message: str

class APIKeyRequest(BaseModel):
    owner_name: str
    admin_key: str

# --- AUTH DEPENDENCY ---
def verify_api_key(request: Request):
    """Dependency to check the Authorization Bearer token or x-api-key header."""
    # Allow localhost bypass for UI debugging in dev mode, but strictly enforce otherwise
    # Since this is an Enterprise Server, let's enforce always unless it's strictly a UI file
    
    auth_header = request.headers.get("Authorization", "")
    api_key = request.headers.get("x-api-key", "")
    
    if auth_header.startswith("Bearer "):
        api_key = auth_header.split(" ")[1]
        
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API Key. Provide via 'x-api-key' header or 'Bearer' token.")
    
    if api_key == ADMIN_KEY:
        return "admin" # Admin bypass
        
    if not auth_manager.validate_key(api_key):
        raise HTTPException(status_code=403, detail="Invalid or Revoked API Key.")
        
    return api_key

# --- ENDPOINTS ---
@app.post("/api/admin/keys/generate")
async def generate_key(req: APIKeyRequest):
    """Admin Only: Generate a new API Key for a user."""
    if req.admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid Master Admin Key.")
        
    new_key = auth_manager.generate_api_key(req.owner_name)
    return {
        "status": "success",
        "owner": req.owner_name,
        "api_key": new_key,
        "message": "Keep this key secure. It will not be shown again."
    }

@app.get("/api/admin/keys/list")
async def list_keys(admin_key: str):
    """Admin Only: List all active keys."""
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid Master Admin Key.")
    
    rows = auth_manager.list_keys()
    keys = [{"id": r[0], "owner": r[1], "created_at": r[2], "active": r[3], "calls": r[4]} for r in rows]
    return {"keys": keys}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest, api_key: str = Depends(verify_api_key)):
    """Streaming Chat endpoint powered by the H200 GPU Cluster."""
    logger.info(f"Incoming request from authenticated key ({request.message[:30]}...)")
    
    def event_stream():
        try:
            for text_chunk in brain.process_request(request.message):
                yield text_chunk
        except Exception as e:
            logger.error(f"Generation error: {e}")
            yield f"\n[SYSTEM ERROR]: {str(e)}"
            
    return StreamingResponse(event_stream(), media_type="text/plain")

@app.get("/api/system/status")
async def get_system_status():
    """Unauthenticated system status ping."""
    return {
        "status": "online",
        "cluster": "H200_GPU_ARRAY",
        "models_active": [
            os.environ.get("LLM_MODEL_GENERAL", "llama3.1:70b"),
            os.environ.get("LLM_MODEL_CODING", "qwen2.5-coder:72b"),
            os.environ.get("LLM_MODEL_VISION", "llama3.2-vision:90b")
        ]
    }

# Provide the UI (Public, but UI will need a key or hardcoded admin key)
# Normally you'd secure this, but let's just mount static.
app.mount("/", StaticFiles(directory="ui", html=True), name="ui")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting H200 API Server on 0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
