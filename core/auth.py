"""
JITD AI — MongoDB Database Layer
==================================
Full user auth, sessions, conversations, messages.
Uses MongoDB Atlas (free tier, cloud-persisted).

Set environment variable:
  MONGODB_URI=mongodb+srv://user:pass@cluster0.xxxxx.mongodb.net/jitd_ai
"""

import os
import secrets
import string
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger

try:
    from pymongo import MongoClient, DESCENDING
    from pymongo.errors import DuplicateKeyError
    MONGO_AVAILABLE = True
except ImportError:
    MONGO_AVAILABLE = False
    logger.warning("pymongo not installed — run: pip install pymongo[srv]")

# ── Connection ────────────────────────────────────────────────
MONGO_URI = os.environ.get(
    "MONGODB_URI",
    "mongodb://localhost:27017/jitd_ai"   # fallback for local dev
)
DB_NAME = os.environ.get("MONGO_DB_NAME", "jitd_ai")

_client = None
_db = None

def get_db():
    global _client, _db
    if _db is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        _db = _client[DB_NAME]
    return _db

def init_db():
    """Initialize collections, indexes, and default admin."""
    db = get_db()

    # Unique indexes
    db.users.create_index("username", unique=True)
    db.users.create_index("email",    unique=True)
    db.users.create_index("api_key",  unique=True)
    db.sessions.create_index("token", unique=True)
    db.sessions.create_index("expires_at", expireAfterSeconds=0)  # TTL index
    db.conversations.create_index([("user_id", DESCENDING), ("updated_at", DESCENDING)])
    db.messages.create_index("conversation_id")

    # Default admin account
    admin_key = os.environ.get("ADMIN_MASTER_KEY", "sk-admin-jitd-ai-master-999")
    if not db.users.find_one({"username": "admin"}):
        db.users.insert_one({
            "username":   "admin",
            "email":      "admin@jitd.ai",
            "password":   _hash("admin123"),
            "api_key":    admin_key,
            "role":       "admin",
            "created_at": datetime.utcnow(),
            "is_active":  True,
            "total_calls": 0,
            "google_id":  None,
            "avatar_url": None,
        })
        logger.info("✅ Admin account created: admin / admin123")
    else:
        logger.info("Admin account exists")

    logger.info(f"✅ MongoDB connected → {DB_NAME}")

# ── Helpers ───────────────────────────────────────────────────
def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def _gen_key() -> str:
    chars = string.ascii_letters + string.digits
    return "sk-jitd-" + "".join(secrets.choice(chars) for _ in range(32))

def _gen_token() -> str:
    return secrets.token_hex(32)

def _user_out(doc) -> dict:
    """Convert MongoDB doc to clean user dict."""
    if not doc:
        return {}
    return {
        "id":          str(doc["_id"]),
        "username":    doc.get("username", ""),
        "email":       doc.get("email", ""),
        "api_key":     doc.get("api_key", ""),
        "role":        doc.get("role", "student"),
        "created_at":  doc.get("created_at", datetime.utcnow()).isoformat(),
        "is_active":   doc.get("is_active", True),
        "total_calls": doc.get("total_calls", 0),
        "avatar_url":  doc.get("avatar_url"),
    }

# ── Public Auth API ───────────────────────────────────────────
def register_user(username: str, email: str, password: str) -> dict:
    db = get_db()
    try:
        api_key = _gen_key()
        doc = {
            "username":    username.strip().lower(),
            "email":       email.strip().lower(),
            "password":    _hash(password),
            "api_key":     api_key,
            "role":        "student",
            "created_at":  datetime.utcnow(),
            "is_active":   True,
            "total_calls": 0,
            "google_id":   None,
            "avatar_url":  None,
        }
        db.users.insert_one(doc)
        logger.info(f"New user: {username}")
        return {"success": True, "api_key": api_key, "user": _user_out(doc)}
    except DuplicateKeyError as e:
        if "username" in str(e):
            return {"success": False, "error": "Username already taken"}
        return {"success": False, "error": "Email already registered"}

def login_user(username: str, password: str) -> dict:
    db = get_db()
    pw_hash = _hash(password)
    user = db.users.find_one({
        "$or": [{"username": username.lower()}, {"email": username.lower()}],
        "password": pw_hash,
        "is_active": True,
    })
    if not user:
        return {"success": False, "error": "Invalid username or password"}

    token = _gen_token()
    expires = datetime.utcnow() + timedelta(days=7)
    db.sessions.insert_one({
        "token":      token,
        "user_id":    user["_id"],
        "created_at": datetime.utcnow(),
        "expires_at": expires,
    })
    return {"success": True, "token": token, "user": _user_out(user)}

def validate_session(token: str) -> Optional[dict]:
    db = get_db()
    session = db.sessions.find_one({
        "token": token,
        "expires_at": {"$gt": datetime.utcnow()}
    })
    if not session:
        return None
    user = db.users.find_one({"_id": session["user_id"], "is_active": True})
    return _user_out(user) if user else None

def validate_api_key(key: str) -> Optional[dict]:
    db = get_db()
    user = db.users.find_one({"api_key": key, "is_active": True})
    if user:
        db.users.update_one({"_id": user["_id"]}, {"$inc": {"total_calls": 1}})
    return _user_out(user) if user else None

def list_users() -> list:
    db = get_db()
    return [_user_out(u) for u in db.users.find().sort("created_at", DESCENDING)]

def delete_user(user_id: str) -> bool:
    db = get_db()
    from bson import ObjectId
    try:
        db.users.update_one(
            {"_id": ObjectId(user_id), "role": {"$ne": "admin"}},
            {"$set": {"is_active": False}}
        )
        return True
    except Exception:
        return False

def get_stats() -> dict:
    db = get_db()
    total  = db.users.count_documents({"is_active": True})
    students = db.users.count_documents({"is_active": True, "role": "student"})
    agg    = list(db.users.aggregate([{"$group": {"_id": None, "total": {"$sum": "$total_calls"}}}]))
    total_calls = agg[0]["total"] if agg else 0
    return {"total_users": total, "students": students, "total_calls": total_calls}

# ── Conversations ─────────────────────────────────────────────
def create_conversation(user_id: str) -> dict:
    db = get_db()
    from bson import ObjectId
    doc = {
        "user_id":    ObjectId(user_id) if isinstance(user_id, str) and len(user_id) == 24 else user_id,
        "title":      "New conversation",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    result = db.conversations.insert_one(doc)
    return {"id": str(result.inserted_id), "title": doc["title"]}

def list_conversations(user_id: str) -> list:
    db = get_db()
    from bson import ObjectId
    uid = ObjectId(user_id) if isinstance(user_id, str) and len(user_id) == 24 else user_id
    rows = db.conversations.find({"user_id": uid}).sort("updated_at", DESCENDING).limit(50)
    return [{"id": str(r["_id"]), "title": r["title"],
             "created_at": r["created_at"].isoformat(),
             "updated_at": r["updated_at"].isoformat()} for r in rows]

def get_messages(conv_id: str, user_id: str) -> Optional[list]:
    db = get_db()
    from bson import ObjectId
    conv = db.conversations.find_one({"_id": ObjectId(conv_id)})
    if not conv:
        return None
    msgs = db.messages.find({"conversation_id": ObjectId(conv_id)}).sort("_id", 1)
    return [{"role": m["role"], "content": m["content"],
             "model": m.get("model"), "time": m["created_at"].isoformat()} for m in msgs]

def save_message(conv_id: str, role: str, content: str, title: str = None):
    db = get_db()
    from bson import ObjectId
    cid = ObjectId(conv_id)
    db.messages.insert_one({
        "conversation_id": cid,
        "role":            role,
        "content":         content,
        "created_at":      datetime.utcnow(),
    })
    update = {"$set": {"updated_at": datetime.utcnow()}}
    if title:
        update["$set"]["title"] = title
    db.conversations.update_one({"_id": cid}, update)

def delete_conversation(conv_id: str, user_id: str) -> bool:
    db = get_db()
    from bson import ObjectId
    db.messages.delete_many({"conversation_id": ObjectId(conv_id)})
    db.conversations.delete_one({"_id": ObjectId(conv_id)})
    return True

# ── Backward-compat shim ──────────────────────────────────────
class AuthManager:
    def __init__(self, db_path=None):
        init_db()
