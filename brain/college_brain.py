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
        # Always use localhost with http:// prefix — 0.0.0.0 doesn't work as client address
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        if not host.startswith("http"):
            host = f"http://localhost:11434"  # Force correct format
        self.ollama_host = "http://localhost:11434"  # Always localhost for client
        self.model_general = os.environ.get("LLM_MODEL_GENERAL", "llama3.1:70b")
        self.model_coding = os.environ.get("LLM_MODEL_CODING", "qwen2.5-coder:32b")
        self.model_vision = os.environ.get("LLM_MODEL_VISION", "llama3.2-vision:90b")

        
        logger.info(f"🧠 Massive Cluster Brain Online.")
        logger.info(f"General Model: {self.model_general}")
        logger.info(f"Coding Model: {self.model_coding}")
        logger.info(f"Vision Model: {self.model_vision}")

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

    def process_request(self, prompt: str, image_b64: Optional[str] = None):
        """Generates the response using the best H200 optimized model."""
        
        if image_b64:
            # Force Vision model if image is present
            target_model = self.model_vision
            logger.info(f"Image attached. Routing to Massive Vision Model: {target_model}")
            system_prompt = "You are a state-of-the-art multimodal AI running on an H200 cluster. Analyze the image carefully."
        else:
            intent = self._determine_expert(prompt)
            if intent == 'coding':
                target_model = self.model_coding
                system_prompt = "You are the world's most advanced Coding AI running on an NVIDIA H200 GPU supercluster. Provide hyper-accurate, robust, and clean code."
            else:
                target_model = self.model_general
                system_prompt = "You are an Enterprise AI running on an NVIDIA H200 GPU supercluster. Provide deep, analytical, and highly structured insights. You rival or exceed GPT-4 scale."

        # Make the request to Ollama
        payload = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": True,
            "options": {
                "temperature": float(os.environ.get("LLM_TEMPERATURE", 0.6)),
                "num_ctx": int(os.environ.get("LLM_CONTEXT_WINDOW", 128000)),
                "num_predict": int(os.environ.get("LLM_MAX_TOKENS", 8192))
            }
        }
        
        if image_b64:
            # Add image correctly per Ollama API specs
            payload["messages"][1]["images"] = [image_b64.split(",")[-1]] 

        logger.info(f"Generating streaming response via {target_model}...")
        
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
