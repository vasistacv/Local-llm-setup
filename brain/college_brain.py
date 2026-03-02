"""
🧠 College AI Enterprise (H200 Server Brain)
=============================================
Intelligent routing across massive GPU clusters.
Handles 70B+ param models for Coding, General, and Vision tasks.
"""

import os
import json
import base64
import requests
from typing import Dict, Any, List, Optional
from loguru import logger
from config.config import settings

class CollegeBrain:
    def __init__(self):
        # Always use localhost with http:// prefix
        self.ollama_host = "http://localhost:11434"
        self.model_general = os.environ.get("LLM_MODEL_GENERAL", "llama3.1:70b")
        self.model_coding  = os.environ.get("LLM_MODEL_CODING",  "qwen2.5-coder:32b")

        logger.info("🧠 College AI Brain Online.")
        logger.info(f"General Model : {self.model_general}")
        logger.info(f"Coding Model  : {self.model_coding}")

        self.routing_prompt = """
        You are the Master Router for an Enterprise AI Cluster (H200 GPUs).
        Analyze the user prompt and decide the best expert model to handle it.
        
        Available Experts:
        1. 'coding' - For writing, debugging, explaining, or generating code.
        2. 'general' - For essays, general knowledge, summarizing, analysis, logic.

        If the prompt contains an image, it skips you and goes straight to 'vision'.
        
        ONLY output a valid JSON like this: {"intent": "coding", "confidence": 0.95}
        """

    def _determine_expert(self, prompt: str) -> str:
        """Uses a quick routing prompt to select the specialized massive model."""
        try:
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.model_general, # General handles logic easily
                    "prompt": prompt,
                    "system": self.routing_prompt,
                    "stream": False,
                    "format": "json"
                }
            )
            data = response.json()
            intent = json.loads(data['response']).get('intent', 'general')
            logger.info(f"Router classified prompt as: {intent.upper()}")
            return intent
        except Exception as e:
            logger.error(f"Routing failed, defaulting to general: {e}")
            return "general"

    def process_request(self, prompt: str):
        """Route to best model and stream the response."""

        intent = self._determine_expert(prompt)
        if intent == 'coding':
            target_model = self.model_coding
            system_prompt = "You are the world's most advanced Coding AI on an NVIDIA H200 GPU. Provide clean, accurate, efficient code with clear explanations."
        else:
            target_model = self.model_general
            system_prompt = "You are an elite enterprise AI on an NVIDIA H200 GPU supercluster. Provide deep, accurate, well-structured answers that rival GPT-4."

        payload = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": prompt}
            ],
            "stream": True,
            "options": {
                "temperature": float(os.environ.get("LLM_TEMPERATURE", 0.6)),
                "num_ctx": 8192,
                "num_predict": int(os.environ.get("LLM_MAX_TOKENS", 4096))
            }
        }

        logger.info(f"Streaming via {target_model}...")
        response = requests.post(
            f"{self.ollama_host}/api/chat",
            json=payload,
            stream=True
        )
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    if 'message' in chunk and 'content' in chunk['message']:
                        yield chunk['message']['content']
                except json.JSONDecodeError:
                    pass
