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
import sqlite3, os
from pathlib import Path

from core.auth import (AuthManager, register_user, login_user,
                       validate_session, validate_api_key, list_users,
                       delete_user, get_stats, init_db)
from brain.college_brain import CollegeBrain

app = FastAPI(title="JITD AI", version="6.0", docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

ADMIN_KEY = os.environ.get("ADMIN_MASTER_KEY", "sk-admin-college-ai-h200-master-999")
DB_PATH   = os.environ.get("API_DB_PATH", "data/memory/api_keys.db")

brain = CollegeBrain()
AuthManager(DB_PATH)

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
    conversation_id: Optional[int] = None

class APIKeyReq(BaseModel):
    owner_name: str
    admin_key: str

# ── Auth Helpers ───────────────────────────────────────────
def _get_conn():
    db = Path(DB_PATH)
    db.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(db))

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
    conn = _get_conn()
    try:
        rows = conn.execute("""
            SELECT id, title, created_at, updated_at FROM conversations
            WHERE user_id=? ORDER BY updated_at DESC LIMIT 50
        """, (user["id"],)).fetchall()
        return {"conversations": [{"id": r[0], "title": r[1],
                "created_at": r[2], "updated_at": r[3]} for r in rows]}
    finally:
        conn.close()

@app.post("/conversations")
async def new_conv(user: dict = Depends(get_current_user)):
    conn = _get_conn()
    try:
        cur = conn.execute("INSERT INTO conversations (user_id) VALUES (?)", (user["id"],))
        conn.commit()
        return {"id": cur.lastrowid, "title": "New conversation"}
    finally:
        conn.close()

@app.get("/conversations/{conv_id}/messages")
async def get_messages(conv_id: int, user: dict = Depends(get_current_user)):
    conn = _get_conn()
    try:
        # Verify ownership
        conv = conn.execute("SELECT id FROM conversations WHERE id=? AND user_id=?",
                            (conv_id, user["id"])).fetchone()
        if not conv:
            raise HTTPException(404, "Conversation not found")
        rows = conn.execute("""
            SELECT role, content, model_used, created_at FROM messages
            WHERE conversation_id=? ORDER BY id ASC
        """, (conv_id,)).fetchall()
        return {"messages": [{"role": r[0], "content": r[1],
                "model": r[2], "time": r[3]} for r in rows]}
    finally:
        conn.close()

@app.delete("/conversations/{conv_id}")
async def delete_conv(conv_id: int, user: dict = Depends(get_current_user)):
    conn = _get_conn()
    try:
        conn.execute("DELETE FROM messages WHERE conversation_id=?", (conv_id,))
        conn.execute("DELETE FROM conversations WHERE id=? AND user_id=?", (conv_id, user["id"]))
        conn.commit()
        return {"status": "deleted"}
    finally:
        conn.close()

# ── Chat Endpoint ──────────────────────────────────────────
@app.post("/chat")
async def chat(req: ChatReq, user: dict = Depends(get_current_user)):
    logger.info(f"[{user.get('username')}] → {req.message[:50]}...")

    # Get or create conversation
    conn = _get_conn()
    conv_id = req.conversation_id
    if not conv_id:
        cur = conn.execute("INSERT INTO conversations (user_id) VALUES (?)", (user["id"],))
        conv_id = cur.lastrowid
        conn.commit()

    # Save user message
    conn.execute("INSERT INTO messages (conversation_id, role, content) VALUES (?,?,?)",
                 (conv_id, "user", req.message))
    conn.execute("UPDATE users SET total_calls=total_calls+1 WHERE id=?", (user["id"],))
    conn.commit()

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
            # Save assistant response
            response_text = "".join(full_response)
            if response_text:
                try:
                    c = _get_conn()
                    # Auto-title from first message
                    title = req.message[:50] + ("…" if len(req.message) > 50 else "")
                    c.execute("UPDATE conversations SET title=?, updated_at=datetime('now') WHERE id=?",
                              (title, conv_id))
                    c.execute("INSERT INTO messages (conversation_id, role, content) VALUES (?,?,?)",
                              (conv_id, "assistant", response_text))
                    c.commit()
                    c.close()
                except Exception as ex:
                    logger.error(f"Save error: {ex}")
            conn.close()

    return StreamingResponse(event_stream(),
                             media_type="text/plain",
                             headers={"X-Conversation-Id": str(conv_id)})

# ── Admin Endpoints (server-side role check) ───────────────
@app.get("/api/admin/users")
async def admin_users(admin: dict = Depends(require_admin)):
    return {"users": list_users()}

@app.delete("/api/admin/users/{uid}")
async def admin_del_user(uid: int, admin: dict = Depends(require_admin)):
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
