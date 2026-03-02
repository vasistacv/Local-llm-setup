"""
🧠 JITD AI Brain
==================
Intelligent routing to specialized models via Ollama.
Supports MOCK mode for local dev without Ollama installed.

Environment:
  OLLAMA_MOCK=true          → Use mock responses (local dev)
  OLLAMA_HOST=http://...    → Ollama server URL
  LLM_MODEL_GENERAL=...     → General model name
  LLM_MODEL_CODING=...      → Coding model name
"""

import os
import json
import time
import requests
from loguru import logger

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

MOCK_MODE   = os.environ.get("OLLAMA_MOCK", "false").lower() == "true"
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

_MOCK_RESPONSES = {
    "coding": [
        "Here's a clean implementation:\n\n```python\ndef solution(data):\n    # Process input\n    result = []\n    for item in data:\n        result.append(item * 2)\n    return result\n```\n\nThis runs in O(n) time with O(n) space complexity. Let me know if you need any modifications!",
        "```javascript\nconst fetchData = async (url) => {\n  try {\n    const response = await fetch(url);\n    const data = await response.json();\n    return data;\n  } catch (error) {\n    console.error('Error:', error);\n    throw error;\n  }\n};\n```\n\nThis uses async/await for clean error handling.",
    ],
    "general": [
        "That's a great question! **JITD AI** is designed to give you expert-level answers across all domains.\n\n### Key Points:\n- Powered by state-of-the-art language models\n- Intelligently routes your query to the best model\n- Provides structured, detailed responses\n\nFeel free to ask me anything — coding, analysis, research, or general knowledge!",
        "Let me break this down clearly:\n\n1. **First**, understand the core concept\n2. **Second**, apply it to your specific case\n3. **Third**, validate the results\n\nThis approach ensures accuracy and completeness. Would you like me to elaborate on any point?",
    ],
}

_mock_idx = {"coding": 0, "general": 0}


class CollegeBrain:
    def __init__(self):
        self.ollama_host   = OLLAMA_HOST
        self.model_general = os.environ.get("LLM_MODEL_GENERAL", "qwen2.5:14b")
        self.model_coding  = os.environ.get("LLM_MODEL_CODING",  "qwen2.5-coder:14b")
        self.mock          = MOCK_MODE or not self._ollama_alive()

        if self.mock:
            logger.warning("⚡ JITD AI running in MOCK mode (Ollama not connected)")
            logger.warning("   Set OLLAMA_MOCK=false and start Ollama for real AI")
        else:
            logger.info("🧠 JITD AI Brain Online — Ollama connected")
            logger.info(f"   General : {self.model_general}")
            logger.info(f"   Coding  : {self.model_coding}")

    def _ollama_alive(self) -> bool:
        """Check if Ollama is reachable."""
        try:
            r = requests.get(f"{self.ollama_host}/api/tags", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def _route(self, prompt: str) -> str:
        """Route to 'coding' or 'general' model."""
        coding_kw = ["code", "function", "class", "debug", "error", "python",
                     "javascript", "java", "sql", "api", "algorithm", "program",
                     "script", "bash", "html", "css", "react", "import", "def ",
                     "fix", "bug", "compile"]
        p = prompt.lower()
        if any(kw in p for kw in coding_kw):
            logger.info("Router → CODING model")
            return "coding"
        # For longer prompts, try LLM routing
        if not self.mock and len(prompt) > 30:
            try:
                r = requests.post(f"{self.ollama_host}/api/generate", json={
                    "model": self.model_general,
                    "prompt": prompt,
                    "system": 'Reply ONLY with valid JSON: {"intent": "coding"} or {"intent": "general"}',
                    "stream": False, "format": "json"
                }, timeout=5)
                intent = json.loads(r.json()["response"]).get("intent", "general")
                logger.info(f"Router → {intent.upper()} model")
                return intent
            except Exception:
                pass
        logger.info("Router → GENERAL model")
        return "general"

    def process_request(self, prompt: str):
        """Route and stream response. Yields text chunks."""
        intent = self._route(prompt)

        if self.mock:
            yield from self._mock_stream(intent, prompt)
            return

        if intent == "coding":
            model  = self.model_coding
            system = ("You are JITD AI, an expert coding assistant. "
                      "Write clean, well-commented, production-ready code. "
                      "Format code in markdown fenced blocks.")
        else:
            model  = self.model_general
            system = ("You are JITD AI, an advanced enterprise AI assistant. "
                      "Provide structured, accurate, insightful responses with "
                      "proper markdown formatting including headers and bullet points.")

        logger.info(f"Streaming via {model}")
        try:
            response = requests.post(
                f"{self.ollama_host}/api/chat",
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user",   "content": prompt},
                    ],
                    "stream": True,
                    "options": {
                        "temperature": float(os.environ.get("LLM_TEMPERATURE", "0.7")),
                        "num_ctx":     8192,
                        "num_predict": int(os.environ.get("LLM_MAX_TOKENS", "4096")),
                    }
                },
                stream=True, timeout=120
            )
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if "message" in chunk and "content" in chunk["message"]:
                            yield chunk["message"]["content"]
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            yield "\n\n⚠️ **AI model is temporarily unavailable.** Please check that Ollama is running.\n"

    def _mock_stream(self, intent: str, prompt: str):
        """Simulate streaming for local dev."""
        responses = _MOCK_RESPONSES[intent]
        idx       = _mock_idx[intent] % len(responses)
        _mock_idx[intent] += 1
        text = f"*(Mock mode — Ollama not running)*\n\n" + responses[idx]
        # Stream word by word
        for word in text.split(" "):
            yield word + " "
            time.sleep(0.04)
