"""
JITD AI — Enterprise Server v6
================================
- Full auth (password + Google OAuth ready)
- Chat history with conversations
- Admin panel (role-protected, not URL-based)
- Streaming AI responses
"""

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
from loguru import logger
import os

from core.auth import (AuthManager, register_user, login_user,
                       validate_session, validate_api_key, list_users,
                       delete_user, get_stats, init_db,
                       create_conversation, list_conversations,
                       get_messages, save_message, delete_conversation)
from brain.college_brain import CollegeBrain

app = FastAPI(title="JITD AI", version="6.0", docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

ADMIN_KEY = os.environ.get("ADMIN_MASTER_KEY", "sk-admin-jitd-ai-master-999")

brain = CollegeBrain()
AuthManager()   # Connects to MongoDB and creates indexes + admin account

# ── Pydantic Models ────────────────────────────────────────
class RegisterReq(BaseModel):
    username: str
    email: str
    password: str

class LoginReq(BaseModel):
    username: str
    password: str

class ChatReq(BaseModel):
    message: str
    conversation_id: Optional[str] = None   # MongoDB ObjectId string

class APIKeyReq(BaseModel):
    owner_name: str
    admin_key: str

# ── Auth Helpers ───────────────────────────────────────────
def get_current_user(request: Request) -> dict:
    token = request.headers.get("Authorization", "")
    if token.startswith("Bearer "):
        user = validate_session(token[7:])
        if user:
            return user
    key = request.headers.get("x-api-key", "")
    if key:
        if key == ADMIN_KEY:
            return {"id": 0, "username": "admin", "role": "admin",
                    "api_key": ADMIN_KEY, "email": "admin@jitd.ai"}
        user = validate_api_key(key)
        if user:
            return user
    raise HTTPException(401, "Not authenticated. Please login.")

def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(403, "Admin access required.")
    return user

# ── Auth Endpoints ─────────────────────────────────────────
@app.post("/auth/register")
async def register(req: RegisterReq):
    if len(req.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters.")
    result = register_user(req.username, req.email, req.password)
    if not result["success"]:
        raise HTTPException(400, result["error"])
    return result

@app.post("/auth/login")
async def login(req: LoginReq):
    result = login_user(req.username, req.password)
    if not result["success"]:
        raise HTTPException(401, result["error"])
    return result

@app.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return user

# ── Conversation / Chat History ────────────────────────────
@app.get("/conversations")
async def list_convs(user: dict = Depends(get_current_user)):
    return {"conversations": list_conversations(user["id"])}

@app.post("/conversations")
async def new_conv(user: dict = Depends(get_current_user)):
    return create_conversation(user["id"])

@app.get("/conversations/{conv_id}/messages")
async def conv_messages(conv_id: str, user: dict = Depends(get_current_user)):
    msgs = get_messages(conv_id, user["id"])
    if msgs is None:
        raise HTTPException(404, "Conversation not found")
    return {"messages": msgs}

@app.delete("/conversations/{conv_id}")
async def del_conv(conv_id: str, user: dict = Depends(get_current_user)):
    delete_conversation(conv_id, user["id"])
    return {"status": "deleted"}

# ── Chat Endpoint ──────────────────────────────────────────
@app.post("/chat")
async def chat(req: ChatReq, user: dict = Depends(get_current_user)):
    logger.info(f"[{user.get('username')}] → {req.message[:50]}...")

    # Get or create conversation
    conv_id = req.conversation_id
    if not conv_id:
        new = create_conversation(user["id"])
        conv_id = new["id"]

    # Save user message
    save_message(conv_id, "user", req.message)

    full_response = []

    def event_stream():
        try:
            for chunk in brain.process_request(req.message):
                full_response.append(chunk)
                yield chunk
        except Exception as e:
            logger.error(f"Generation error: {e}")
            yield f"\n[Error]: {str(e)}"
        finally:
            response_text = "".join(full_response)
            if response_text:
                try:
                    title = req.message[:50] + ("…" if len(req.message) > 50 else "")
                    save_message(conv_id, "assistant", response_text, title=title)
                except Exception as ex:
                    logger.error(f"Save error: {ex}")

    return StreamingResponse(event_stream(),
                             media_type="text/plain",
                             headers={"X-Conversation-Id": str(conv_id)})

# ── Admin Endpoints (server-side role check) ───────────────
@app.get("/api/admin/users")
async def admin_users(admin: dict = Depends(require_admin)):
    return {"users": list_users()}

@app.delete("/api/admin/users/{uid}")
async def admin_del_user(uid: str, admin: dict = Depends(require_admin)):
    delete_user(uid)
    return {"status": "deactivated"}

@app.get("/api/admin/stats")
async def admin_stats(admin: dict = Depends(require_admin)):
    return get_stats()

@app.post("/api/admin/keys/generate")
async def gen_key(req: APIKeyReq):
    if req.admin_key != ADMIN_KEY:
        raise HTTPException(403, "Invalid admin key.")
    import secrets
    result = register_user(req.owner_name, f"{req.owner_name}@jitd.ai", secrets.token_hex(8))
    return {"api_key": result.get("api_key"), "owner": req.owner_name}

@app.get("/api/system/status")
async def status():
    return {"status": "online", "service": "JITD AI",
            "models": {"general": "qwen2.5:14b", "coding": "qwen2.5-coder:14b"}}

# ── Static UI ──────────────────────────────────────────────
app.mount("/", StaticFiles(directory="ui", html=True), name="ui")

if __name__ == "__main__":
    import uvicorn
    init_db()
    logger.info("🚀 JITD AI Server starting on 0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
