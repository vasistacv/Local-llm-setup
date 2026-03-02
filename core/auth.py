"""
Core Authentication & User Management System
=============================================
Full user accounts: signup, login, JWT sessions,
admin dashboard, per-student API keys.
"""
import sqlite3
import hashlib
import secrets
import string
import os
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger

DB_PATH = os.environ.get("API_DB_PATH", "data/memory/api_keys.db")

def _get_conn():
    db = Path(DB_PATH)
    db.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(db))

def init_db():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    UNIQUE NOT NULL,
            email       TEXT    UNIQUE NOT NULL,
            password    TEXT    NOT NULL,
            api_key     TEXT    UNIQUE NOT NULL,
            role        TEXT    DEFAULT 'student',
            created_at  TEXT    DEFAULT (datetime('now')),
            is_active   INTEGER DEFAULT 1,
            total_calls INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS sessions (
            token       TEXT PRIMARY KEY,
            user_id     INTEGER NOT NULL,
            created_at  TEXT DEFAULT (datetime('now')),
            expires_at  TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS chat_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            role        TEXT NOT NULL,
            content     TEXT NOT NULL,
            model_used  TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()

    # Create default admin account if not exists
    admin_key = os.environ.get("ADMIN_MASTER_KEY", "sk-admin-college-ai-h200-master-999")
    pw_hash = _hash_password("admin123")
    try:
        conn.execute("""
            INSERT OR IGNORE INTO users (username, email, password, api_key, role)
            VALUES ('admin', 'admin@college.ai', ?, ?, 'admin')
        """, (pw_hash, admin_key))
        conn.commit()
        logger.info("Admin account ready: admin / admin123")
    except Exception as e:
        logger.warning(f"Admin init: {e}")
    conn.close()

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def _generate_key() -> str:
    chars = string.ascii_letters + string.digits
    return "sk-col-" + "".join(secrets.choice(chars) for _ in range(32))

def _generate_token() -> str:
    return secrets.token_hex(32)

# ── Public API ─────────────────────────────────────────────

def register_user(username: str, email: str, password: str) -> dict:
    conn = _get_conn()
    try:
        api_key = _generate_key()
        pw_hash = _hash_password(password)
        conn.execute("""
            INSERT INTO users (username, email, password, api_key, role)
            VALUES (?, ?, ?, ?, 'student')
        """, (username.strip().lower(), email.strip().lower(), pw_hash, api_key))
        conn.commit()
        user = conn.execute("SELECT * FROM users WHERE username=?", (username.strip().lower(),)).fetchone()
        logger.info(f"New user registered: {username}")
        return {"success": True, "api_key": api_key, "user": _user_dict(user)}
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            return {"success": False, "error": "Username already taken"}
        return {"success": False, "error": "Email already registered"}
    finally:
        conn.close()

def login_user(username: str, password: str) -> dict:
    conn = _get_conn()
    try:
        pw_hash = _hash_password(password)
        user = conn.execute("""
            SELECT * FROM users WHERE (username=? OR email=?) AND password=? AND is_active=1
        """, (username.lower(), username.lower(), pw_hash)).fetchone()

        if not user:
            return {"success": False, "error": "Invalid username or password"}

        token = _generate_token()
        expires = (datetime.utcnow() + timedelta(days=7)).isoformat()
        conn.execute("INSERT INTO sessions (token, user_id, expires_at) VALUES (?,?,?)",
                     (token, user[0], expires))
        conn.commit()
        return {"success": True, "token": token, "user": _user_dict(user)}
    finally:
        conn.close()

def validate_session(token: str) -> dict | None:
    conn = _get_conn()
    try:
        row = conn.execute("""
            SELECT u.* FROM users u
            JOIN sessions s ON u.id = s.user_id
            WHERE s.token=? AND s.expires_at > datetime('now') AND u.is_active=1
        """, (token,)).fetchone()
        return _user_dict(row) if row else None
    finally:
        conn.close()

def validate_api_key(key: str) -> dict | None:
    conn = _get_conn()
    try:
        row = conn.execute("SELECT * FROM users WHERE api_key=? AND is_active=1", (key,)).fetchone()
        if row:
            conn.execute("UPDATE users SET total_calls=total_calls+1 WHERE id=?", (row[0],))
            conn.commit()
        return _user_dict(row) if row else None
    finally:
        conn.close()

def list_users() -> list:
    conn = _get_conn()
    try:
        rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
        return [_user_dict(r) for r in rows]
    finally:
        conn.close()

def delete_user(user_id: int) -> bool:
    conn = _get_conn()
    try:
        conn.execute("UPDATE users SET is_active=0 WHERE id=? AND role!='admin'", (user_id,))
        conn.commit()
        return True
    finally:
        conn.close()

def get_stats() -> dict:
    conn = _get_conn()
    try:
        total = conn.execute("SELECT COUNT(*) FROM users WHERE is_active=1").fetchone()[0]
        students = conn.execute("SELECT COUNT(*) FROM users WHERE role='student' AND is_active=1").fetchone()[0]
        total_calls = conn.execute("SELECT SUM(total_calls) FROM users").fetchone()[0] or 0
        return {"total_users": total, "students": students, "total_calls": total_calls}
    finally:
        conn.close()

def _user_dict(row) -> dict:
    if not row:
        return {}
    return {
        "id": row[0], "username": row[1], "email": row[2],
        "api_key": row[4], "role": row[5],
        "created_at": row[6], "is_active": row[7], "total_calls": row[8]
    }

# ── Backward compatibility for sessions ────────────────────
class AuthManager:
    def __init__(self, db_path=None):
        global DB_PATH
        if db_path:
            DB_PATH = db_path
        init_db()

    def generate_api_key(self, owner: str) -> str:
        result = register_user(owner, f"{owner}@college.ai", secrets.token_hex(8))
        return result.get("api_key", "")

    def validate_key(self, key: str) -> bool:
        return validate_api_key(key) is not None

    def list_keys(self):
        users = list_users()
        return [(u["id"], u["username"], u["created_at"], u["is_active"], u["total_calls"]) for u in users]
