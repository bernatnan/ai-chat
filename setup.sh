#!/bin/bash
set -e

echo "========================================="
echo "  AI Chat Stack - Script de Configuració"
echo "========================================="

# Comprovar si existeix .env
if [ ! -f .env ]; then
    echo "[1/6] Creant .env des de la plantilla..."
    cp .env.template .env

    # Generar secrets
    JWT_SECRET=$(openssl rand -hex 32)
    JWT_REFRESH_SECRET=$(openssl rand -hex 32)
    CREDS_KEY=$(openssl rand -hex 32)
    CREDS_IV=$(openssl rand -hex 16)
    MEILI_KEY=$(openssl rand -hex 32)
    SEARXNG_SECRET=$(openssl rand -hex 32)
    ADMIN_PANEL_SECRET=$(openssl rand -hex 32)

    # Reemplaçar placeholders
    sed -i "s/GENERATE_JWT_SECRET/$JWT_SECRET/" .env
    sed -i "s/GENERATE_JWT_REFRESH_SECRET/$JWT_REFRESH_SECRET/" .env
    sed -i "s/GENERATE_CREDS_KEY/$CREDS_KEY/" .env
    sed -i "s/GENERATE_CREDS_IV/$CREDS_IV/" .env
    sed -i "s/GENERATE_MEILI_KEY/$MEILI_KEY/" .env
    sed -i "s/GENERATE_SEARXNG_SECRET/$SEARXNG_SECRET/" .env
    sed -i "s/GENERATE_ADMIN_PANEL_SECRET/$ADMIN_PANEL_SECRET/" .env

    echo "  -> Secrets generats!"
    echo ""
    echo "  IMPORTANT: Editar .env ara per configurar:"
    echo "    - DOMAIN_CLIENT i DOMAIN_SERVER (el teu domini)"
    echo "    - API keys per Qwen, DeepSeek, Anthropic, Zhipu AI"
    echo "    - TAVILY_API_KEY (scraper de cerca web - https://tavily.com)"
    echo "    - JINA_API_KEY (reranker de cerca web - https://jina.ai/api-dashboard/)"
    echo "    - Configuració SMTP (opcional)"
    echo ""
    echo "  Executa: nano .env"
    echo ""
    read -p "  Prem ENTER quan estiguis a punt per continuar..."
else
    echo "[1/6] .env ja existeix, saltant..."
fi

# Inicialitzar submòduls
echo "[2/6] Inicialitzant submòduls git..."
git submodule update --init --recursive
echo "  -> Fet!"

# Crear directoris necessaris
echo "[3/6] Creant directoris..."
mkdir -p data-node meili_data uploads logs images skill
echo "  -> Fet!"

# Construir i iniciar contenidors
echo "[4/6] Construint i iniciant contenidors..."
docker compose up -d --build
echo "  -> Contenidors iniciats!"

# Esperar que els serveis estiguin llestos
echo "[5/6] Esperant que els serveis estiguin llestos..."
sleep 15

# Comprovar si Ollama s'està executant
echo "[6/6] Comprovant estat d'Ollama..."
if docker exec ollama ollama list > /dev/null 2>&1; then
    echo "  -> Ollama està llest!"
else
    echo "  -> Ollama s'està iniciant (pot trigar una estona)..."
fi

echo ""
echo "========================================="
echo "  Configuració Completada!"
echo "========================================="
echo ""
echo "AI Chat Stack s'està executant a: http://localhost:3080"
echo ""
echo "Propers passos:"
echo "  1. Crear el primer usuari administrador:"
echo "     docker compose exec api npm run create-user"
echo ""
echo "  2. Descarregar models d'Ollama (opcional):"
echo "     docker exec -it ollama ollama pull llama3.2"
echo "     docker exec -it ollama ollama pull qwen2.5"
echo "     docker exec -it ollama ollama pull deepseek-r1"
echo ""
echo "  3. Configurar Apache2 com a reverse proxy (veure docs/apache2.conf.example)"
echo ""
echo "  4. Activar Cloudflare Turnstile (editar librechat.yaml)"
echo ""
echo "  5. Provar la cerca web:"
echo "     SearXNG s'està executant a: http://localhost:8080"
echo "     Assegura't d'haver configurat TAVILY_API_KEY i JINA_API_KEY a .env"
echo ""
