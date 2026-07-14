#!/bin/bash
set -e

echo "========================================="
echo "  AI Chat Stack - Setup Script"
echo "========================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "[1/6] Creating .env from template..."
    cp .env.template .env

    # Generate secrets
    JWT_SECRET=$(openssl rand -hex 32)
    JWT_REFRESH_SECRET=$(openssl rand -hex 32)
    CREDS_KEY=$(openssl rand -hex 32)
    CREDS_IV=$(openssl rand -hex 16)
    MEILI_KEY=$(openssl rand -hex 32)
    SEARXNG_SECRET=$(openssl rand -hex 32)
    ADMIN_PANEL_SECRET=$(openssl rand -hex 32)

    # Replace placeholders
    sed -i "s/GENERATE_JWT_SECRET/$JWT_SECRET/" .env
    sed -i "s/GENERATE_JWT_REFRESH_SECRET/$JWT_REFRESH_SECRET/" .env
    sed -i "s/GENERATE_CREDS_KEY/$CREDS_KEY/" .env
    sed -i "s/GENERATE_CREDS_IV/$CREDS_IV/" .env
    sed -i "s/GENERATE_MEILI_KEY/$MEILI_KEY/" .env
    sed -i "s/GENERATE_SEARXNG_SECRET/$SEARXNG_SECRET/" .env
    sed -i "s/GENERATE_ADMIN_PANEL_SECRET/$ADMIN_PANEL_SECRET/" .env

    echo "  -> Secrets generated!"
    echo ""
    echo "  IMPORTANT: Edit .env now to configure:"
    echo "    - DOMAIN_CLIENT and DOMAIN_SERVER (your domain)"
    echo "    - API keys for Qwen, DeepSeek, Anthropic, Zhipu AI"
    echo "    - TAVILY_API_KEY (web search scraper - https://tavily.com)"
    echo "    - JINA_API_KEY (web search reranker - https://jina.ai/api-dashboard/)"
    echo "    - SMTP settings (optional)"
    echo ""
    echo "  Run: nano .env"
    echo ""
    read -p "  Press ENTER when ready to continue..."
else
    echo "[1/6] .env already exists, skipping..."
fi

# Initialize submodules
echo "[2/6] Initializing git submodules..."
git submodule update --init --recursive
echo "  -> Done!"

# Create necessary directories
echo "[3/6] Creating directories..."
mkdir -p data-node meili_data uploads logs images skill
echo "  -> Done!"

# Build and start containers
echo "[4/6] Building and starting containers..."
docker compose up -d --build
echo "  -> Containers started!"

# Wait for services to be ready
echo "[5/6] Waiting for services to be ready..."
sleep 15

echo "[6/6] Pulling Whisper STT model for LocalAI..."
if docker exec localai sh -c 'curl -L -o /build/models/ggml-tiny.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin' 2>/dev/null; then
    echo "  -> Whisper model downloaded!"
else
    echo "  -> Whisper model download skipped (will download on first request)"
fi

echo ""
echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo ""
echo "AI Chat Stack is running at: http://localhost:3080"
echo ""
echo "Next steps:"
echo "  1. Create the first admin user:"
echo "     docker compose exec api npm run create-user"
echo ""
echo "  2. Test STT (speech-to-text):"
echo "     Say something in the chat and try the microphone button"
echo ""
echo "  3. Pull Ollama models (optional):"
echo "     docker exec -it ollama ollama pull llama3.2"
echo "     docker exec -it ollama ollama pull qwen2.5"
echo "     docker exec -it ollama ollama pull deepseek-r1"
echo ""
echo "  4. Configure Apache2 reverse proxy (see docs/apache2.conf.example)"
echo ""
echo "  5. Enable Cloudflare Turnstile (edit librechat.yaml)"
echo ""
echo "  6. Test web search:"
echo "     SearXNG is running at: http://localhost:8080"
echo "     Make sure you've configured TAVILY_API_KEY and JINA_API_KEY in .env"
echo ""
