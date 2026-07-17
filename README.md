# AI Chat Stack

Self-hosted AI chat platform built on [LibreChat](https://github.com/danny-avila/LibreChat) with additional services for web search, image generation, and local models.

## Features

- **Multi-provider AI**: Anthropic, Qwen, DeepSeek, Zhipu AI, and local models via Ollama
- **Integrated web search**: SearXNG (local) + Tavily (scraper) + Jina (reranker)
- **Image generation**: Qwen Image 2.0 Pro via MCP server
- **Document generation**: Create PDF and Markdown documents from text, markdown, or HTML via MCP server
- **Generated Files Manager**: All generated documents and images are automatically indexed and accessible from a dedicated **Generated Files** view (Files → Generated tab). Files are served via the API with per-user access control.
- **Local models**: Ollama with GPU (NVIDIA) or CPU support
- **Admin Panel**: User, group, role, and configuration management from the browser
- **User management**: Admin-only registration, roles, and granular permissions
- **Bot protection**: Cloudflare Turnstile (client-side)
- **RAG**: Retrieval-Augmented Generation with pgvector
- **Full-text search**: Meilisearch for conversation search
- **Privacy**: All data stored locally
- **Conversation migration**: Scripts to convert conversations from OpenWebUI and other platforms

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Apache2 / NGINX                 │
│              (Reverse Proxy + SSL)               │
└──────────────────────┬──────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│  LibreChat   │ │  Ollama  │ │   SearXNG    │
│  (API + UI)  │ │  (Local  │ │  (Web Search │
│   :3080      │ │   LLMs)  │ │    Engine)   │
└──────┬───────┘ │  :11434  │ │   :8080      │
       │         └──────────┘ └──────────────┘
       │
  ┌────┴────────────────────────────┐
  │                                 │
  ▼              ▼         ▼        ▼
┌──────┐  ┌──────────┐ ┌──────┐ ┌────────┐
│Mongo │  │Meilisearch│ │Vector│ │RAG API │
│ :DB  │  │  :7700    │ │ :DB  │ │ :8000  │
└──────┘  └──────────┘ └──────┘ └────────┘
```

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/bernatnan/ai-chat.git
cd ai-chat

# 2. Run setup (generates secrets and creates .env)
./setup.sh

# 3. Edit .env to configure API keys and domain
nano .env

# 4. Create the first admin user
docker compose exec api npm run create-user

# 5. Download Ollama models (optional)
docker exec -it ollama ollama pull llama3.2
```

See [DEPLOY.md](DEPLOY.md) for the complete deployment guide.

## Included Services

| Service | Port | Description | Local? |
|---------|------|-------------|:------:|
| LibreChat | 3080 | Web interface + API | ✅ |
| Admin Panel | 3000 | User, group, role management | ✅ |
| MongoDB | - | Conversation database | ✅ |
| Meilisearch | 7700 | Full-text search | ✅ |
| PostgreSQL (pgvector) | - | Vector database (RAG) | ✅ |
| RAG API | 8000 | Retrieval-Augmented Generation | ✅ |
| Ollama | 11434 | Local AI models | ✅ |
| SearXNG | 8080 | Web search engine | ✅ |
| Valkey | - | Cache for SearXNG | ✅ |

## AI Providers

| Provider | Type | Models |
|----------|------|--------|
| **Anthropic** | Cloud (API key) | Claude Sonnet, Opus, Haiku |
| **OpenAI** | Cloud (API key) | GPT-4o, GPT-4, GPT-3.5, o1 |
| **Qwen** | Cloud (API key) | Qwen Max, Plus, Turbo, VL |
| **DeepSeek** | Cloud (API key) | DeepSeek Chat, Reasoner |
| **Zhipu AI** | Cloud (API key) | GLM-4 Plus, Air, Flash |
| **Ollama** | Local | Llama, Mistral, Qwen, DeepSeek-R1 |

## Web Search

Web search uses 3 components:

| Component | Service | Description | Local? |
|-----------|---------|-------------|:------:|
| **Search** | SearXNG | Meta-search engine (Google, DuckDuckGo, etc.) | ✅ |
| **Scraper** | Tavily | Extracts content from web pages | ❌ (API) |
| **Reranker** | Jina | Reranks results by relevance | ❌ (API) |

## Image Generation

The **qwen-image-2.0-pro** model is integrated via MCP server. Users can generate and edit images by requesting it from agents.

## Document Generation

The **document-generator** MCP server allows creating PDF and Markdown documents from text, markdown, or HTML content.

### Features

- **Markdown Generation**: Create `.md` files from any text format
- **PDF Generation**: Create `.pdf` files with automatic formatting
- **Smart Content Detection**: Automatically detects plain text, markdown, or HTML
- **Flexible Input**: Accepts content in plain text, markdown, or HTML format

### Usage

Users can request document generation from agents or directly in chat:

```
User: Create a PDF document with the following content:
"# Project Report

## Summary
This project has achieved all its goals.

## Key Metrics
- Completion: 100%
- Budget: On track
- Timeline: Ahead of schedule"

AI: [Calls generate_pdf tool]
```

### Output Location

Generated documents are saved to `/app/uploads/documents/` and can be downloaded from the LibreChat interface.

### Technical Details

- **Dependencies**: `pdfkit` (PDF generation), `marked` (Markdown parser)
- **Configuration**: Set `DOCUMENTS_PATH` environment variable to customize output directory
- **Timeout**: 120 seconds per document generation

See [document-generator README](librechat/mcp-servers/document-generator/README.md) for detailed documentation.

## Model Configuration

### Default Models

Default models for each provider are configured in `librechat.yaml`:

```yaml
endpoints:
  custom:
    - name: 'Qwen'
      models:
        default:
          - 'qwen-max'
          - 'qwen-plus'
          # ...
        fetch: true  # Fetches available models from API
```

### Model Selection in UI

- **`fetch: true`**: LibreChat downloads the complete model list from the API. Users can select any model from the interface.
- **`fetch: false`**: Only models listed in `models.default` are shown.

Currently, **Qwen** and **Ollama** have `fetch: true`, the rest have `fetch: false`.

### File Analysis with Any Model

If you want PDFs and other documents to work with models that do **not** support native file input, use an **Agent** with the `file_search` capability enabled.

How it works:
- The uploaded file is stored and embedded through the RAG API
- LibreChat queries the vector database for relevant chunks
- Only the retrieved text context is sent to the model

This means you can analyze PDFs with models such as Qwen, DeepSeek, or local Ollama models, even when they do not support direct `file` message parts.

Required environment variables:

```bash
RAG_API_URL=http://rag_api:8000
RAG_OPENAI_BASEURL=http://ollama:11434/v1
RAG_OPENAI_API_KEY=ollama
RAG_USE_FULL_CONTEXT=false
EMBEDDINGS_PROVIDER=openai
EMBEDDINGS_MODEL=nomic-embed-text
```

Recommended local embeddings model:

```bash
docker exec -it ollama ollama pull nomic-embed-text
```

Recommended workflow:
1. Create an Agent using the model you want
2. Ensure the Agent has `file_search` enabled
3. Upload the PDF to the Agent, not to a plain chat
4. Ask questions about the file

### Changing Default Models

Edit `librechat.yaml` and modify the `models.default` list for the provider you want. Then restart:

```bash
docker compose restart api
```

### Why All Endpoints Are Custom?

In this project, **all AI providers (including Anthropic and OpenAI) are configured as custom endpoints**, not as LibreChat native endpoints.

**Reason**: LibreChat has a design limitation that prevents controlling which models each user group sees when using native endpoints. The `ENDPOINTS` variable in `.env` globally controls which native endpoints are loaded, but doesn't allow restricting them by role or group.

By configuring all providers as custom endpoints:
- ✅ **Granular control**: Each `librechat.yaml.X` file defines exactly which models are available
- ✅ **Group flexibility**: Different users can have access to different models
- ✅ **Consistency**: All providers are configured the same way
- ⚠️ **Limitation**: Some native LibreChat optimizations for Anthropic and OpenAI are lost (like specific message formatting), but basic functionality works correctly

**Configuration file strategy**:
- `librechat.yaml` - Base configuration without Turnstile (versioned in git)
- `librechat.yaml.local` - Base configuration with Turnstile (NOT versioned, for server)
- `librechat.yaml.basic` - Limited access (only Qwen Plus)
- `librechat.yaml.standard` - Standard access (Qwen basic + DeepSeek + Ollama)
- `librechat.yaml.admin` - Full access (all providers and models)

To activate Turnstile on the server:
```bash
cp librechat.yaml librechat.yaml.local
nano librechat.yaml.local  # Add turnstile section with your key
```

To switch between configurations:
```bash
cp librechat.yaml.admin librechat.yaml
docker compose restart api
```

## Cloudflare Turnstile

Cloudflare Turnstile is available as bot protection for login and registration forms.

### Configuration

Edit `librechat.yaml` and uncomment the Turnstile section:

```yaml
turnstile:
  siteKey: "YOUR_SITE_KEY"
  options:
    language: "ca"
    size: "normal"
```

### Security Limitation

**Important**: The current LibreChat implementation only validates the Turnstile token **client-side**. There is no server-side token verification.

**Implications**:
- ✅ Blocks casual bots and basic automation
- ❌ Does not protect against direct API attacks (an attacker can send requests without going through the widget)

**Recommendation**: For personal use with `ALLOW_REGISTRATION=false`, the risk is minimal. The real security is in user control (only admin can create accounts).

## Requirements

- Docker and Docker Compose
- NVIDIA GPU with drivers + NVIDIA Container Toolkit (optional, for Ollama with GPU)
- Minimum 8GB RAM (16GB recommended)
- 50GB disk space
- **Note**: Ollama works with CPU (without GPU), but performance is lower

## Roadmap

### Phase 1: Initial Setup (current) ✅

- [x] LibreChat with multi-provider (Anthropic, Qwen, DeepSeek, Zhipu AI)
- [x] Ollama for local models
- [x] SearXNG for local web search
- [x] Tavily as scraper (API)
- [x] Jina as reranker (API)
- [x] Qwen Image via MCP server
- [x] Admin-only registration
- [x] Cloudflare Turnstile (optional)

### Phase 2: Replace APIs with Local Services

- [ ] **Local scraper**: Replace Tavily with Firecrawl self-hosted
  - Requires ~12GB additional RAM
  - 5 new containers (API, Playwright, Redis, RabbitMQ, PostgreSQL)
  - 100% local and private
  
- [ ] **Local reranker**: Replace Jina with local model
  - Model: `jinaai/jina-reranker-v3` (~600MB)
  - Server: HuggingFace TEI or similar
  - Requires adapter/proxy for LibreChat compatibility
  - Works with CPU (doesn't need GPU)

### Phase 3: Optimization and Scalability

- [ ] **Redis for caching**: Add Redis to improve performance
- [ ] **Automatic backup**: Scheduled backup script for MongoDB and uploads
- [ ] **Monitoring**: Integrate Prometheus + Grafana
- [ ] **Centralized logs**: ELK stack or similar
- [ ] **Multi-tenant**: Configure advanced groups and permissions

### Phase 4: Advanced Features

- [ ] **Voice**: Local speech-to-text and text-to-speech (Whisper, Piper)
- [ ] **Code Interpreter**: Code execution in sandbox
- [ ] **Advanced agents**: Additional MCP servers, subagents
- [ ] **Fine-tuning**: Train local models with custom data
- [ ] **Federation**: Connect with other instances (future)

## Project Structure

```
ai-chat/
├── docker-compose.yml          # Orchestrates all services
├── .env.template               # Configuration template
├── librechat.yaml              # LibreChat configuration
├── setup.sh                    # Installation script
├── DEPLOY.md                   # Deployment guide
├── README.md                   # This file
├── searxng/
│   └── settings.yml            # SearXNG configuration
├── docs/
│   └── apache2.conf.example    # Apache2 configuration
└── librechat/                  # Git submodule → LibreChat fork
    ├── Dockerfile.custom       # Image with MCP server
    ├── mcp-servers/
    │   └── qwen-image/         # MCP server for Qwen Image
    └── ...
```

## User Management

With `ALLOW_REGISTRATION=false`, only admin can create users:

```bash
# Create user
docker compose exec api npm run create-user

# Invite by email
docker compose exec api npm run invite-user user@example.com

# List users
docker compose exec api npm run list-users
```

## Conversation Migration

The project includes scripts to convert conversations from other platforms (like OpenWebUI) to LibreChat-compatible format.

### Available Scripts

**Format diagnostics:**
```bash
# Analyzes a JSON file to identify the format
python3 scripts/diagnose_import.py conversation.json
```

**OpenWebUI → LibreChat conversion:**
```bash
# Converts OpenWebUI exports to LibreChat format
python3 scripts/openwebui_to_librechat.py openwebui_export.json
```

### How to Import Conversations

1. **Export** conversations from OpenWebUI (JSON format)
2. **Convert** the file with the script:
   ```bash
   python3 scripts/openwebui_to_librechat.py openwebui_export.json
   ```
3. **Import** to LibreChat:
   - Go to Settings → Data Controls → Import Conversations
   - Select the generated `_librechat.json` file

### Supported Formats

**Native (no conversion needed):**
- LibreChat (native)
- ChatGPT (OpenAI)
- ChatbotUI
- Claude (Anthropic)

**Require conversion:**
- OpenWebUI → Use `openwebui_to_librechat.py`

See [scripts/README.md](scripts/README.md) for more details.

## Docker Installation (Debian)

Official Docker repository, not the outdated Debian package.

```bash
# 1. Remove old Docker packages
for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do
  sudo apt remove -y "$pkg" 2>/dev/null || true
done

# 2. Install prerequisites
sudo apt update
sudo apt install -y ca-certificates curl

# 3. Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# 4. Add the repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 6. Add your user to the docker group
sudo usermod -aG docker $USER
newgrp docker

# 7. Verify
docker --version
docker compose version
docker run hello-world
```

## Deploy on New Server

Full deployment from scratch (e.g., after moving disks to new hardware).

```bash
# 1. Already done if you followed Docker Installation above
sudo apt install git

# 2. Clone the repository
cd /srv
git clone https://github.com/bernatnan/ai-chat.git
cd ai-chat

# 3. Init submodules
git submodule update --init --recursive

# 4. Restore non-versioned files (optional, if migrating from existing server)
# See Backup section below for restic setup
# scripts/restore.sh

# 5. If restoring from a MongoDB 4.4 backup, migrate before starting:
# scripts/migrate-mongodb.sh
#   or specify custom versions:
#   scripts/migrate-mongodb.sh 4.4 8.0.20
# Then follow the on-screen instructions (edit docker-compose.yml, mongorestore)

# 6. Start all services
# Nota: si el contenidor api no pot escriure a logs/ (EACCES), executa:
#   sudo chown -R 1000:1000 /srv/ai-chat/logs/
docker compose up -d

# 6. Create admin user
docker compose exec api npm run create-user

# 7. Verify health
curl http://localhost:3080
curl http://localhost:8080  # SearXNG
curl http://localhost:11434 # Ollama
curl http://localhost:8180/readyz  # LocalAI
curl http://localhost:8180/v1/models  # Should show whisper-1 and tts-1

# 8. Download Whisper STT model (if empty)
docker exec localai sh -c 'curl -L -o /build/models/ggml-tiny.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin'

# 9. Set up backups
# See Backup section below
```

### Restoring from backup (migrating or recovery)

```bash
# 1. Clone and init submodules
git clone https://github.com/bernatnan/ai-chat.git /srv/ai-chat
cd /srv/ai-chat
git submodule update --init --recursive

# 2. Install restic and set up environment
# See Backup section below for setup

# 3. Restore non-versioned files (data-node, uploads, images, .env, librechat.yaml)
scripts/restore.sh            # from remote (default)
# scripts/restore.sh local    # from local repo instead

# 4. If restoring from a MongoDB 4.4 backup, migrate before starting:
# scripts/migrate-mongodb.sh
#   or specify custom versions:
#   scripts/migrate-mongodb.sh 4.4 8.0.20
# Then follow the on-screen instructions

# 5. Start all services
docker compose up -d

# 6. Download Whisper STT model (if empty)
docker exec localai sh -c 'curl -L -o /build/models/ggml-tiny.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin'
```

A maximum of 4 steps: `git clone`, `scripts/restore.sh`, `scripts/migrate-mongodb.sh`, `docker compose up -d`.

## Backup

Daily encrypted backups using [Restic](https://restic.net/). Supports two independent targets — **local** (LAN Debian) and/or **remote** (S3-compatible, e.g. iDrive E2). Each can be enabled/disabled via env vars.

### What's backed up

| Path | Contents | Why |
|---|---|---|
| `data-node/` | MongoDB database | Conversations, users, config overrides |
| `uploads/` | User uploaded files | Images, documents, audio |
| `images/` | Generated images | MCP-generated content |
| `.env` | Environment secrets | API keys, tokens |
| `librechat.yaml` | Local LibreChat config | Gitignored, not in repo |

No versionats — només els fitxers que **no** estan a Git. La resta es recupera amb `git clone`.

### Setup

```bash
# 1. Install restic
sudo apt install restic

# 2. Create password file
echo 'your-secure-password' | sudo tee /root/.restic/restic-password.txt
sudo chmod 600 /root/.restic/restic-password.txt
# Or use passage:
# passage insert restic/librechat

# 3. Copy environment template and edit
sudo mkdir -p /root/.restic
sudo cp scripts/restic-env.sh.template /root/.restic/restic-env.sh
sudo vim /root/.restic/restic-env.sh

# 4. Initialize repositories
# Note: these paths must match RESTIC_REPO_LOCAL and RESTIC_REPO_REMOTE in restic-env.sh
restic -r /mnt/backup/librechat init
restic -r s3:us-east-1.linodeobjects.com/librechat-backup init

# 5. Copy cron file
sudo cp scripts/restic-cron /etc/cron.d/restic-backup

# 6. Test manually
sudo /srv/ai-chat/scripts/backup.sh
```

### Toggling targets

Edit `/root/.restic/restic-env.sh`:

```bash
export BACKUP_LOCAL=true   # set to false to skip local
export BACKUP_REMOTE=true  # set to false to skip remote
```

### Files

See:
- [`scripts/backup.sh`](scripts/backup.sh) — backup only non-versioned files
- [`scripts/restore.sh`](scripts/restore.sh) — restore on a new server (3-step deploy)
- [`scripts/restic-env.sh.template`](scripts/restic-env.sh.template) — environment config template
- [`scripts/restic-exclude.txt`](scripts/restic-exclude.txt) — exclusion patterns (legacy)
- [`scripts/migrate-mongodb.sh`](scripts/migrate-mongodb.sh) — migrate MongoDB 4.4 data to 8.0

## Updates

```bash
# Update project and submodules
git pull
git submodule update --remote --merge
docker compose pull
docker compose up -d --build
```

## Troubleshooting

### Permission denied (EACCES) a logs/

El contenidor LibreChat s'executa amb l'usuari `node` (UID 1000). Si Docker crea el directori `logs/` com a `root`, l'escriptura falla:

```bash
sudo chown -R 1000:1000 /srv/ai-chat/logs/
docker compose restart api
```

### STT / whisper model not found (500 error)

Si STT falla amb `stat /build/models/ggml-tiny.bin: no such file or directory`, descarrega el model manualment:

```bash
docker exec localai sh -c 'curl -L -o /build/models/ggml-tiny.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin'
```

## Contributions

This is a personal project. If you find bugs or have suggestions, open an issue.

## License

- **AI Chat Stack**: MIT
- **LibreChat**: MIT (see [librechat/LICENSE](librechat/LICENSE))
- **SearXNG**: AGPL-3.0

## Useful Links

- [LibreChat Docs](https://librechat.ai/docs)
- [SearXNG Docs](https://docs.searxng.org/)
- [Ollama Docs](https://github.com/ollama/ollama/tree/main/docs)
- [Tavily API](https://docs.tavily.com/)
- [Jina AI](https://jina.ai/)
