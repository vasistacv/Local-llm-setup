"""
College AI Enterprise - Full Server
=====================================
Endpoints:
  POST /auth/register   - Create student account
  POST /auth/login      - Login (returns session token)
  GET  /auth/me         - Get current user info
  POST /chat            - Stream AI response
  GET  /api/admin/users - List all users (admin)
  DELETE /api/admin/users/{id} - Deactivate user (admin)
  GET  /api/admin/stats - System stats (admin)
  GET  /api/system/status - Public status
"""

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from loguru import logger
import os

from core.auth import (AuthManager, register_user, login_user,
                       validate_session, validate_api_key, list_users,
                       delete_user, get_stats, init_db)
from brain.college_brain import CollegeBrain
from config.config import settings

app = FastAPI(title="College AI Enterprise", version="5.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

ADMIN_KEY = os.environ.get("ADMIN_MASTER_KEY", "sk-admin-college-ai-h200-master-999")

brain = CollegeBrain()
auth_manager = AuthManager(os.environ.get("API_DB_PATH", "data/memory/api_keys.db"))

# ── Request Models ─────────────────────────────────────────
class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    message: str

class APIKeyRequest(BaseModel):
    owner_name: str
    admin_key: str

# ── Auth Helpers ───────────────────────────────────────────
def get_current_user(request: Request) -> dict:
    """Validate session token OR api key. Returns user dict."""
    # Check session token
    token = request.headers.get("Authorization", "")
    if token.startswith("Bearer "):
        token = token[7:]
        user = validate_session(token)
        if user:
            return user

    # Check API key header
    api_key = request.headers.get("x-api-key", "")
    if api_key:
        if api_key == ADMIN_KEY:
            return {"id": 0, "username": "admin", "role": "admin", "api_key": ADMIN_KEY}
        user = validate_api_key(api_key)
        if user:
            return user

    raise HTTPException(401, "Not authenticated. Please login or provide API key.")

def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(403, "Admin access required.")
    return user

# ── Auth Endpoints ─────────────────────────────────────────
@app.post("/auth/register")
async def register(req: RegisterRequest):
    if len(req.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters.")
    result = register_user(req.username, req.email, req.password)
    if not result["success"]:
        raise HTTPException(400, result["error"])
    return result

@app.post("/auth/login")
async def login(req: LoginRequest):
    result = login_user(req.username, req.password)
    if not result["success"]:
        raise HTTPException(401, result["error"])
    return result

@app.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return user

# ── Chat Endpoint ──────────────────────────────────────────
@app.post("/chat")
async def chat(req: ChatRequest, user: dict = Depends(get_current_user)):
    logger.info(f"Chat from {user.get('username')} → {req.message[:40]}...")

    def event_stream():
        try:
            for chunk in brain.process_request(req.message):
                yield chunk
        except Exception as e:
            logger.error(f"Generation error: {e}")
            yield f"\n[ERROR]: {str(e)}"

    return StreamingResponse(event_stream(), media_type="text/plain")

# ── Admin Endpoints ────────────────────────────────────────
@app.get("/api/admin/users")
async def admin_list_users(admin: dict = Depends(require_admin)):
    return {"users": list_users()}

@app.delete("/api/admin/users/{user_id}")
async def admin_delete_user(user_id: int, admin: dict = Depends(require_admin)):
    delete_user(user_id)
    return {"status": "deactivated", "user_id": user_id}

@app.get("/api/admin/stats")
async def admin_stats(admin: dict = Depends(require_admin)):
    return get_stats()

@app.post("/api/admin/keys/generate")
async def generate_key(req: APIKeyRequest):
    if req.admin_key != ADMIN_KEY:
        raise HTTPException(403, "Invalid Admin Key.")
    result = register_user(req.owner_name, f"{req.owner_name}@college.ai",
                           __import__("secrets").token_hex(8))
    return {"api_key": result.get("api_key"), "owner": req.owner_name}

@app.get("/api/admin/keys/list")
async def list_keys(admin_key: str):
    if admin_key != ADMIN_KEY:
        raise HTTPException(403, "Invalid Admin Key.")
    return {"keys": [{"id": u["id"], "owner": u["username"],
                      "created": u["created_at"], "active": u["is_active"],
                      "calls": u["total_calls"]} for u in list_users()]}

# ── Status ─────────────────────────────────────────────────
@app.get("/api/system/status")
async def status():
    return {
        "status": "online",
        "models": {"general": "qwen2.5:14b", "coding": "qwen2.5-coder:14b"},
        "gpu":    "NVIDIA H200 MIG 16GB"
    }

# ── Static UI ──────────────────────────────────────────────
app.mount("/", StaticFiles(directory="ui", html=True), name="ui")

if __name__ == "__main__":
    import uvicorn
    init_db()
    logger.info("🚀 College AI Enterprise v5 — Starting on 0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
