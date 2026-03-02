#!/bin/bash
# ══════════════════════════════════════════════════════════════
#  JITD AI — Complete Server Setup Script
#  Run this once after git pull on a new Kubeflow workspace
#  Usage: bash setup.sh
# ══════════════════════════════════════════════════════════════

set -e  # Exit on error
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║       JITD AI — Server Setup             ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── 1. Python dependencies ──────────────────────────────────
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt --quiet
echo "✅ Python deps installed"

# ── 2. Node.js (via nvm) ────────────────────────────────────
echo ""
echo "📦 Setting up Node.js..."
export NVM_DIR="$HOME/.nvm"

if [ ! -s "$NVM_DIR/nvm.sh" ]; then
  echo "   Installing nvm..."
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
fi

source "$NVM_DIR/nvm.sh"
nvm install 20 --silent
nvm use 20
echo "✅ Node $(node --version) ready"

# ── 3. Build React frontend ─────────────────────────────────
echo ""
echo "🔨 Building React frontend..."
cd frontend
rm -rf node_modules
npm install --silent
npm run build
cd ..
echo "✅ React frontend built → ui/"

# ── 4. Ollama models ────────────────────────────────────────
echo ""
echo "🤖 Downloading AI models (this takes a few minutes)..."
if command -v ollama &> /dev/null; then
    ollama pull qwen2.5:14b &
    ollama pull qwen2.5-coder:14b &
    wait
    echo "✅ Models ready"
else
    echo "⚠️  Ollama not found — start it first then run:"
    echo "   ollama pull qwen2.5:14b && ollama pull qwen2.5-coder:14b"
fi

# ── 5. Initialize database ──────────────────────────────────
echo ""
echo "🗄️  Initializing database..."
mkdir -p data/memory
python -c "from core.auth import init_db; init_db(); print('✅ Database ready')"

# ── 6. Done ─────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  ✅ Setup complete! Start the server:                ║"
echo "║                                                      ║"
echo "║  python server.py                                    ║"
echo "║                                                      ║"
echo "║  Then expose via Cloudflare:                        ║"
echo "║  ./cloudflared tunnel --url http://localhost:8000    ║"
echo "║                                                      ║"
echo "║  Admin login: admin / admin123                      ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
