import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

class Config:
    """NOVA Configuration Manager - UNIVERSAL FIX"""
    
    def __init__(self):
        # Paths — Dynamic resolution works on BOTH Windows and Linux
        self.BASE_DIR = Path(__file__).parent.parent.resolve()
        self.ENV_FILE = self.BASE_DIR / "config" / "settings.env"
        
        # Load environment variables
        load_dotenv(self.ENV_FILE)
        
        # --- CORE SETTINGS ---
        self.APP_NAME = "NOVA"
        self.VERSION = "1.0.0"
        self.DEBUG = True
        self.VERBOSE_LOGGING = True
        
        # --- PATHS (Standardized) ---
        self.DATA_DIR = self.BASE_DIR / "data"
        self.LOGS_DIR = self.BASE_DIR / "logs"
        self.CONFIG_DIR = self.BASE_DIR / "config"
        self.MEMORY_DB = self.DATA_DIR / "memory" / "nova.db"
        self.MODELS_DIR = self.BASE_DIR / "models"
        self.PIPER_MODEL_DIR = self.MODELS_DIR / "piper" 
        self.SCREENSHOT_DIR = self.DATA_DIR / "screenshots" 
        
        # --- ALIASES (To prevent AttributeErrors) ---
        self.MEMORY_DB_PATH = self.MEMORY_DB # For memory_manager.py
        self.LOG_DIR = self.LOGS_DIR # Possible alias
        
        # Create directories
        for path in [self.DATA_DIR, self.LOGS_DIR, self.CONFIG_DIR, self.MEMORY_DB.parent, self.PIPER_MODEL_DIR, self.SCREENSHOT_DIR]:
            path.mkdir(parents=True, exist_ok=True)

        # --- SECURITY SETTINGS ---
        self.SECURITY_LEVEL = "high"
        self.MAX_RISK_SCORE = 7
        self.SAFE_MODE = False
        self.REQUIRE_CONFIRMATION = True
        self.RESTRICTED_PATHS = [
            Path("C:/Windows"),
            Path("C:/Program Files"),
            Path("C:/Program Files (x86)")
        ]
        
        # --- LOGGING SETTINGS ---
        self.LOG_RETENTION_DAYS = 30
        self.MAX_LOG_SIZE_MB = 10
        self.LOG_COMPRESSION = "zip"
        
        # --- FILE SETTINGS ---
        self.ALLOWED_EXTENSIONS = {'.txt', '.md', '.py', '.json', '.pdf', '.docx', '.csv', '.log', '.png', '.jpg'}
        self.MAX_FILE_SIZE_MB = 50
        
        # --- LLM SETTINGS (Optimized for Speed) ---
        self.LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
        self.LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:8b-instruct-q4_K_M")
        self.LLM_MODEL_GENERAL = os.getenv("LLM_MODEL_GENERAL", "llama3.1:8b-instruct-q4_K_M")
        self.LLM_MODEL_CODING = os.getenv("LLM_MODEL_CODING", "qwen2.5-coder:7b")
        self.OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.LLM_BASE_URL = self.OLLAMA_HOST
        self.LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", 30))
        self.LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.7))
        self.LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", 4096))
        self.MAX_CONVERSATION_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", 50))
        self.LLM_CONTEXT_WINDOW = int(os.getenv("LLM_CONTEXT_WINDOW", 4096))
        
        # --- VOICE & AUDIO SETTINGS ---
        self.STT_MODEL = "base"
        self.STT_LANGUAGE = "en"
        self.STT_DEVICE = "cpu"
        self.SAMPLE_RATE = 16000
        self.ENABLE_GPU = True # GPU for Ollama logic
        self.VOICE_TIMEOUT = 5.0
        self.ENERGY_THRESHOLD = 300
        
        # --- TTS SETTINGS ---
        self.TTS_ENGINE = "pyttsx3" 
        self.TTS_VOICE = "en_US-ryans-medium"
        self.TTS_SPEED = 1.0 
        self.TTS_RATE = 175 
        self.TTS_VOLUME = 1.0
        
        # --- WAKE WORD SETTINGS ---
        self.WAKE_WORD = "nova"
        self.WAKE_WORD_MODEL = "nova_en"
        self.WAKE_WORD_SENSITIVITY = 0.5
        
        # --- AUTOMATION SETTINGS ---
        self.AUTOMATION_ENABLED = True
        self.MOUSE_SPEED = 0.5
        self.SCREENSHOTS_DIR = self.SCREENSHOT_DIR # Alias

    def get_system_prompt(self) -> str:
        """Get the optimized system prompt"""
        return """You are NOVA, a smart and efficient AI assistant.
TRAITS:
1. Concise: Give short, direct answers (1-2 sentences) for voice response.
2. Helpful: Use your tools to execute tasks immediately.
3. Smart: Provide accurate information.

CAPABILITIES:
- Open apps (calculator, notepad, browser)
- Create/Read files
- Search the web
- Remember user details

CURRENT STATE:
- Running locally on Windows
- Voice Mode: ENABLED
- GPU Acceleration: ENABLED (Ollama)

INSTRUCTIONS:
- When asked to do something, JUST DO IT using a tool.
- Don't narrate your plan, just execute.
- If user says "Hi", reply briefly.
"""

    def get(self, key: str, default: Any = None) -> Any:
        return os.getenv(key, getattr(self, key, default))

# Global instance
config = Config()
