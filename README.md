# 🎓 College AI Enterprise System
> A fully offline, enterprise-grade AI assistant powered by local LLMs on an NVIDIA H200 GPU cluster. Deployed via Kubeflow on a college server.

---

## 🚀 System Architecture

```
User Browser / API Client
        │
        ▼
FastAPI Gateway (server.py) ← API Key Auth
        │
        ▼
CollegeBrain Router (brain/college_brain.py)
   ├── General Query  → llama3.1:70b
   ├── Coding Query   → qwen2.5-coder:72b
   └── Image/Vision   → llama3.2-vision (via image_b64)
        │
        ▼
Ollama Engine (running locally on H200 GPU)
```

---

## 📁 Project Structure

```
AI_ASSISTANT/
├── server.py               # FastAPI API Gateway (main entry point)
├── start.py                # One-click deployment script for Kubeflow
├── requirements.txt        # Python dependencies
├── .gitignore
│
├── brain/
│   ├── college_brain.py    # Intelligent model router
│   └── llm.py              # Core LLM communication layer
│
├── config/
│   ├── config.py           # Universal config manager (Windows + Linux)
│   └── settings.env        # Model settings & environment variables
│
├── core/
│   ├── auth.py             # API Key generation & validation (SQLite)
│   └── logger.py           # Logging utilities
│
├── ui/
│   ├── index.html          # Enterprise web interface
│   ├── style.css           # Premium dark theme + glassmorphism
│   └── app.js              # Frontend logic (streaming, vision upload)
│
├── tools/
│   ├── agent.py            # AI agent utilities
│   ├── automation.py       # Task automation
│   ├── executor.py         # Command execution
│   └── security.py         # Security validation
│
├── memory/
│   └── memory_manager.py   # Conversation memory (SQLite)
│
└── voice/
    ├── stt.py              # Speech-to-Text
    ├── tts.py              # Text-to-Speech
    └── wake_word.py        # Wake word detection
```

---

## ⚡ Kubeflow Server Deployment (3 Commands)

### Step 1: Clone the Repository
```bash
git clone https://github.com/vasistacv/Local-llm-setup.git ~/AI_ASSISTANT
cd ~/AI_ASSISTANT
```

### Step 2: Install Ollama (once)
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Step 3: Start the System
```bash
python start.py
```

`start.py` automatically:
- Creates all required directories
- Installs Python packages
- Starts Ollama engine
- Downloads AI models (70B+)
- Launches the API server on **port 8000**

---

## 🤖 AI Models (H200 Optimized)

| Purpose | Model | Why |
|---|---|---|
| General Intelligence | `llama3.1:70b` | GPT-4 level reasoning |
| Coding Expert | `qwen2.5-coder:72b` | World's best open-source coding model |
| Vision (Image) | Auto-routed | Upload image → triggers vision model |

---

## 🔐 API Key System

The system has built-in API key management. You can issue keys to departments or users.

### Generate a Key (Admin only)
```bash
curl -X POST http://localhost:8000/api/admin/keys/generate \
  -H "Content-Type: application/json" \
  -d '{"owner_name": "CS Department", "admin_key": "sk-admin-college-ai-h200-master-999"}'
```

### Use a Key
```bash
curl -X POST http://localhost:8000/chat \
  -H "x-api-key: sk-col-your-key-here" \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain binary trees"}'
```

### Check System Status
```bash
curl http://localhost:8000/api/system/status
```

---

## 🖥️ Web Interface

Access the enterprise UI at: **`http://localhost:8000`**

Features:
- 💬 Streaming chat with automatic model routing
- 📸 Image upload → Vision AI analysis
- 🔑 API Key input in sidebar
- 🔧 Admin panel to generate new keys

---

## ⚙️ Configuration (`config/settings.env`)

| Variable | Default | Description |
|---|---|---|
| `LLM_MODEL_GENERAL` | `llama3.1:70b` | General intelligence model |
| `LLM_MODEL_CODING` | `qwen2.5-coder:72b` | Coding expert model |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama engine URL |
| `ADMIN_MASTER_KEY` | `sk-admin-college-ai-h200-master-999` | Admin key (change in production!) |

---

## 🔧 Requirements

- NVIDIA H200 GPU (or MIG slice with 18GB+ VRAM)
- Python 3.10+
- Ollama installed
- 100GB+ disk space for 70B models

---

## 📌 Notes

- **Offline**: Once models are downloaded, zero internet needed
- **Secure**: API key enforcement on all endpoints
- **Scalable**: Multiple users served via API keys
- **Cross-platform**: Works on Windows (laptop) and Linux (server)
