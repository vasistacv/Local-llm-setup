"""
NOVA Memory System (Phase 5)
==============================
Enterprise memory with SQL + vector search
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from loguru import logger
from typing import List, Dict, Any, Optional
import numpy as np


class MemoryManager:
    """
    Enterprise memory system
    - Short-term: Last N messages
    - Long-term: SQL database
    - Semantic: Vector embeddings (future)
    """
    
    def __init__(self, config):
        self.config = config
        self.db_path = config.MEMORY_DB_PATH
        self.max_short_term = 50
        self.short_term_memory = []
        
        # Initialize database
        self._init_database()
        
        logger.info(f"Memory system initialized: {self.db_path}")
    
    def _init_database(self):
        """Initialize SQLite database schema"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_input TEXT NOT NULL,
                assistant_response TEXT NOT NULL,
                context TEXT,
                session_id TEXT
            )
        """)
        
        # User profile table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profile (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Notes/memories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT NOT NULL,
                tags TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Tasks/reminders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                due_date TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("✓ Database schema initialized")
    
    # ==================== CONVERSATION MEMORY ====================
    
    def remember_conversation(self, user_input: str, assistant_response: str, 
                            context: Dict = None, session_id: str = None):
        """Store conversation turn"""
        # Add to short-term memory
        self.short_term_memory.append({
            "user": user_input,
            "assistant": assistant_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last N messages
        if len(self.short_term_memory) > self.max_short_term:
            self.short_term_memory.pop(0)
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO conversations (timestamp, user_input, assistant_response, context, session_id)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            user_input,
            assistant_response,
            json.dumps(context) if context else None,
            session_id
        ))
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Conversation stored (short-term: {len(self.short_term_memory)})")
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict]:
        """Get recent conversations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, user_input, assistant_response
            FROM conversations
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "timestamp": row[0],
                "user": row[1],
                "assistant": row[2]
            })
        
        conn.close()
        return list(reversed(results))
    
    def get_conversation_context(self) -> List[Dict]:
        """Get short-term memory for context"""
        return self.short_term_memory.copy()
    
    def search_conversations(self, query: str, limit: int = 5) -> List[Dict]:
        """Search past conversations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, user_input, assistant_response
            FROM conversations
            WHERE user_input LIKE ? OR assistant_response LIKE ?
            ORDER BY id DESC
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "timestamp": row[0],
                "user": row[1],
                "assistant": row[2]
            })
        
        conn.close()
        return results
    
    # ==================== USER PROFILE ====================
    
    def save_profile(self, key: str, value: str):
        """Save user profile information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO user_profile (key, value, updated_at)
            VALUES (?, ?, ?)
        """, (key, value, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Profile updated: {key}")
    
    def get_profile(self, key: str) -> Optional[str]:
        """Get user profile information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM user_profile WHERE key = ?", (key,))
        result = cursor.fetchone()
        
        conn.close()
        return result[0] if result else None
    
    def get_all_profile(self) -> Dict[str, str]:
        """Get all profile information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT key, value FROM user_profile")
        profile = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        return profile
    
    # ==================== NOTES ====================
    
    def create_note(self, content: str, title: str = None, tags: List[str] = None) -> int:
        """Create a note"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO notes (title, content, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            title,
            content,
            json.dumps(tags) if tags else None,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        note_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Note created: #{note_id}")
        return note_id
    
    def get_notes(self, limit: int = 10, tag: str = None) -> List[Dict]:
        """Get notes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if tag:
            cursor.execute("""
                SELECT id, title, content, tags, created_at
                FROM notes
                WHERE tags LIKE ?
                ORDER BY id DESC
                LIMIT ?
            """, (f"%{tag}%", limit))
        else:
            cursor.execute("""
                SELECT id, title, content, tags, created_at
                FROM notes
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
        
        notes = []
        for row in cursor.fetchall():
            notes.append({
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "tags": json.loads(row[3]) if row[3] else [],
                "created_at": row[4]
            })
        
        conn.close()
        return notes
    
    def search_notes(self, query: str) -> List[Dict]:
        """Search notes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, content, created_at
            FROM notes
            WHERE title LIKE ? OR content LIKE ?
            ORDER BY id DESC
            LIMIT 10
        """, (f"%{query}%", f"%{query}%"))
        
        notes = []
        for row in cursor.fetchall():
            notes.append({
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "created_at": row[3]
            })
        
        conn.close()
        return notes
    
    # ==================== TASKS ====================
    
    def create_task(self, title: str, description: str = None, due_date: str = None) -> int:
        """Create a task"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO tasks (title, description, due_date, created_at)
            VALUES (?, ?, ?, ?)
        """, (title, description, due_date, datetime.now().isoformat()))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Task created: #{task_id} - {title}")
        return task_id
    
    def get_tasks(self, status: str = "pending") -> List[Dict]:
        """Get tasks"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, description, status, due_date, created_at
            FROM tasks
            WHERE status = ?
            ORDER BY created_at DESC
        """, (status,))
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "status": row[3],
                "due_date": row[4],
                "created_at": row[5]
            })
        
        conn.close()
        return tasks
    
    def complete_task(self, task_id: int):
        """Mark task as complete"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE tasks
            SET status = 'completed', completed_at = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), task_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Task completed: #{task_id}")
    
    # ==================== STATISTICS ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Conversation count
        cursor.execute("SELECT COUNT(*) FROM conversations")
        stats['total_conversations'] = cursor.fetchone()[0]
        
        # Profile entries
        cursor.execute("SELECT COUNT(*) FROM user_profile")
        stats['profile_entries'] = cursor.fetchone()[0]
        
        # Notes count
        cursor.execute("SELECT COUNT(*) FROM notes")
        stats['total_notes'] = cursor.fetchone()[0]
        
        # Tasks count
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
        stats['pending_tasks'] = cursor.fetchone()[0]
        
        # Short-term memory size
        stats['short_term_messages'] = len(self.short_term_memory)
        
        conn.close()
        return stats
    
    def clear_short_term(self):
        """Clear short-term memory"""
        self.short_term_memory = []
        logger.info("Short-term memory cleared")


if __name__ == "__main__":
    # Test memory system
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from config.config import config
    
    memory = MemoryManager(config)
    
    # Test conversation memory
    memory.remember_conversation("What is AI?", "AI is artificial intelligence...")
    memory.remember_conversation("Tell me more", "AI includes machine learning...")
    
    # Test profile
    memory.save_profile("name", "User")
    memory.save_profile("github", "vasistacv")
    
    # Test notes
    memory.create_note("Remember to download Ollama", "Ollama Setup", ["setup", "todo"])
    
    # Test tasks
    memory.create_task("Install Ollama", "Download and install from ollama.ai")
    
    # Get stats
    print("\nMemory Statistics:")
    print(json.dumps(memory.get_stats(), indent=2))
    
    # Get profile
    print("\nUser Profile:")
    print(json.dumps(memory.get_all_profile(), indent=2))
