"""
NOVA Brain - Local LLM Integration
===================================
Interface to local LLM via Ollama
"""

import json
from typing import Dict, Any, Optional, List
import requests
from loguru import logger


class NovaBrain:
    """Local LLM brain using Ollama"""
    
    def __init__(self, config):
        self.config = config
        self.model = config.LLM_MODEL
        self.host = config.OLLAMA_HOST
        self.temperature = config.LLM_TEMPERATURE
        self.max_tokens = config.LLM_MAX_TOKENS
        self.system_prompt = config.get_system_prompt()
        
        # Conversation history
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = config.MAX_CONVERSATION_HISTORY
        
        # Check if Ollama is running
        self._check_ollama()
    
    def _check_ollama(self):
        """Check if Ollama server is running"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info(f"✓ Ollama connected at {self.host}")
                
                # Check if our model is available
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                
                if not any(self.model in name for name in model_names):
                    logger.warning(f"⚠️  Model {self.model} not found!")
                    logger.info(f"Available models: {', '.join(model_names)}")
                    logger.info(f"Run: ollama pull {self.model}")
                else:
                    logger.info(f"✓ Model {self.model} ready")
            else:
                logger.error("Ollama server responded but with error")
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Cannot connect to Ollama at {self.host}")
            logger.error("Make sure Ollama is running: ollama serve")
        except Exception as e:
            logger.error(f"Error checking Ollama: {e}")
    
    def _build_messages(self, user_input: str) -> List[Dict[str, str]]:
        """Build message list with system prompt and history"""
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add recent history
        for msg in self.conversation_history[-10:]:  # Last 10 messages
            messages.append(msg)
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    def chat(self, user_input: str, stream: bool = False) -> str:
        """
        Send message to LLM and get response
        
        Args:
            user_input: User's message
            stream: Whether to stream the response
            
        Returns:
            LLM's response
        """
        messages = self._build_messages(user_input)
        
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": stream,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            }
            
            if stream:
                return self._chat_stream(payload)
            else:
                return self._chat_normal(payload)
                
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return "I apologize, but I encountered an error processing your request."
    
    def _chat_normal(self, payload: dict) -> str:
        """Non-streaming chat"""
        response = requests.post(
            f"{self.host}/api/chat",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            assistant_message = result['message']['content']
            
            # Add to history
            self.conversation_history.append({
                "role": "user",
                "content": payload["messages"][-1]["content"]
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            # Trim history if too long
            if len(self.conversation_history) > self.max_history:
                self.conversation_history = self.conversation_history[-self.max_history:]
            
            return assistant_message
        else:
            logger.error(f"Ollama API error: {response.status_code}")
            return "Error communicating with LLM"
    
    def _chat_stream(self, payload: dict) -> str:
        """Streaming chat (for real-time response)"""
        full_response = ""
        
        response = requests.post(
            f"{self.host}/api/chat",
            json=payload,
            stream=True,
            timeout=60
        )
        
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    if 'message' in chunk:
                        content = chunk['message'].get('content', '')
                        full_response += content
                        # Could yield content here for real-time display
                except json.JSONDecodeError:
                    continue
        
        # Add to history
        self.conversation_history.append({
            "role": "user",
            "content": payload["messages"][-1]["content"]
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": full_response
        })
        
        return full_response
    
    def parse_action(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Try to parse JSON action from response
        
        Returns:
            Action dict if found, None otherwise
        """
        try:
            # Try to parse as JSON
            data = json.loads(response)
            if 'action' in data:
                return data['action']
        except json.JSONDecodeError:
            # Response is just text, no action
            pass
        
        return None
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    def get_quick_response(self, prompt: str) -> str:
        """Get a quick, concise response (no history)"""
        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 100
                }
            }
            
            response = requests.post(
                f"{self.host}/api/chat",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()['message']['content']
            else:
                return ""
        except:
            return ""


if __name__ == "__main__":
    # Test the brain
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from config.config import config
    
    brain = NovaBrain(config)
    
    # Test chat
    print("\nTesting NOVA Brain...")
    print("=" * 60)
    
    response = brain.chat("What is machine learning?")
    print(f"NOVA: {response}")
    
    print("\n" + "=" * 60)
    
    # Test action parsing
    action_test = brain.chat("Open Chrome browser")
    print(f"NOVA: {action_test}")
    
    action = brain.parse_action(action_test)
    if action:
        print(f"Action detected: {action}")
