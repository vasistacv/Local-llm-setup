# 🎓 College AI Enterprise System

An advanced, offline-capable AI system designed for educational environments. Features dual-model intelligence, separating high-performance coding tasks from general reasoning.

## ✨ Key Features
*   **Dual-Model Brain**: 
    *   `Llama 3.1 8B` for General Reasoning & Academic Q&A.
    *   `Qwen 2.5 Coder 7B` for High-Efficiency Programming tasks.
*   **Intelligent Routing**: Automatically detects intent and uses the best model.
*   **100% Offline**: No internet required after initial setup.
*   **Premium Web Interface**: Modern, dark-themed UI with streaming responses.

## 🚀 Quick Start

### 1. Initial Setup (One-time)
Run the setup script to install dependencies and download models:
```
START_SETUP.bat
```
*Note: Internet is required for this step only.*

### 2. Launch System
Start the server and access the interface:
```
START_COLLEGE_AI.bat
```
The interface will be available at: `http://localhost:8000`

## 🛠️ Configuration
Edit `config/settings.env` to customize models or parameters:
*   `LLM_MODEL_GENERAL`: Model for chat (default: llama3.1)
*   `LLM_MODEL_CODING`: Model for code (default: qwen2.5-coder)

## 🏗️ Architecture
*   **Frontend**: HTML5/CSS3/JS (No build step required, offline friendly).
*   **Backend**: FastAPI (High performance Python server).
*   **Engine**: Ollama (Local LLM runner).

---
**Enterprise Edition** - Optimized for Accuracy & Performance.
