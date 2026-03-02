"""
🛡️ College AI Enterprise - API Authentication
=============================================
Manages API keys using a local SQLite database.
Allows issuing, revoking, and validating keys for users.
"""

import sqlite3
import secrets
from pathlib import Path
from loguru import logger
import os

class AuthManager:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize the API Keys database table."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_value TEXT UNIQUE NOT NULL,
                    owner_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    total_requests INTEGER DEFAULT 0
                )
            ''')
            conn.commit()

    def generate_api_key(self, owner_name: str) -> str:
        """Generates and stores a new API Key."""
        # Generate a secure random API key prefix with 'sk-college-'
        prefix = "sk-col-"
        random_part = secrets.token_hex(24)
        new_key = f"{prefix}{random_part}"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO api_keys (key_value, owner_name) VALUES (?, ?)",
                (new_key, owner_name)
            )
            conn.commit()
        
        logger.info(f"Generated new API Key for: {owner_name}")
        return new_key

    def validate_key(self, api_key: str) -> bool:
        """Checks if an API key is valid and active. Increments usage tracker."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM api_keys WHERE key_value = ? AND is_active = 1", (api_key,))
            result = cursor.fetchone()
            
            if result:
                # Increment usage
                cursor.execute("UPDATE api_keys SET total_requests = total_requests + 1 WHERE id = ?", (result[0],))
                conn.commit()
                return True
            return False

    def list_keys(self):
        """List all keys (for admin dashboard)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, owner_name, created_at, is_active, total_requests FROM api_keys")
            return cursor.fetchall()
