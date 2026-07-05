# Deployment Guide - AI Chat Stack

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

## Server Requirements

- Docker and Docker Compose installed
- NVIDIA GPU with drivers and NVIDIA Container Toolkit (for Ollama)
- Minimum 8GB RAM (16GB recommended)
- 50GB disk space

## Quick Installation

```bash
# 1. Clone the repository
git clone https://github.com/bernatnan/ai-chat.git
cd ai-chat

# 2. Run setup
./setup.sh

# 3. Create the first admin user
docker compose exec api npm run create-user

# 4. Download Ollama models (optional)
docker exec -it ollama ollama pull llama3.2
docker exec -it ollama ollama pull qwen2.5
docker exec -it ollama ollama pull deepseek-r1
```

## Detailed Configuration

### 1. .env File

The `setup.sh` creates `.env` automatically and generates secrets. Edit it to configure:

```bash
nano .env
```

**Important variables:**

| Variable | Description |
|----------|-------------|
| `DOMAIN_CLIENT` / `DOMAIN_SERVER` | Your public domain (e.g., `https://chat.example.com`) |
| `QWEN_API_KEY` | DashScope API key (Alibaba Cloud) |
| `DEEPSEEK_API_KEY` | DeepSeek API key |
| `ANTHROPIC_API_KEY` | Anthropic API key (or `user_provided`) |
| `ZHIPU_API_KEY` | Zhipu AI API key |
| `TAVILY_API_KEY` | Tavily API key (web scraping) |
| `JINA_API_KEY` | Jina API key (reranker) |

**SMTP (optional):**

```bash
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_ENCRYPTION=starttls
EMAIL_USERNAME=user@example.com
EMAIL_PASSWORD=password
EMAIL_FROM=noreply@example.com
EMAIL_FROM_NAME=LibreChat
```

### 2. librechat.yaml File

Already created with base configuration. Edit it to customize:

```bash
nano librechat.yaml
```

**Cloudflare Turnstile (optional):**

```yaml
turnstile:
  siteKey: "YOUR_SITE_KEY"
  options:
    language: "ca"
    size: "normal"
```

### 3. Apache2 Reverse Proxy with SSL

```bash
# Install required modules (includes ssl and remoteip for Cloudflare)
sudo a2enmod proxy proxy_http proxy_wstunnel rewrite headers ssl remoteip
sudo systemctl restart apache2

# Copy configuration
sudo cp docs/apache2.conf.example /etc/apache2/sites-available/ai-chat.conf
sudo nano /etc/apache2/sites-available/ai-chat.conf
# Edit ServerName and SSL certificate paths

# Enable and reload
sudo a2ensite ai-chat
sudo systemctl reload apache2
```

**Important:**
- In `.env`, configure `TRUST_PROXY=1` and domains with `https://`
- Apache configuration already includes HTTP → HTTPS redirect and Cloudflare proxy support

### 4. SSL with Let's Encrypt

If you don't have the certificate yet:

```bash
sudo apt install certbot python3-certbot-apache
sudo certbot --apache -d chat.example.com
```

### 5. Cloudflare Configuration

If using Cloudflare as DNS proxy (recommended):

1. **DNS**: Enable proxy (orange cloud) for `chat.example.com` and `admin.chat.example.com`
2. **SSL/TLS**: Set mode to **"Full (Strict)"** for maximum security
3. **Page Rules**: Add "Always Use HTTPS" rule
4. **Network**: Ensure "WebSockets" is enabled

**Connection flow with Cloudflare:**
```
Client → Cloudflare (HTTPS) → Apache (HTTPS) → LibreChat (HTTP :3080)
Client → Cloudflare (HTTPS) → Apache (HTTPS) → Admin Panel (HTTP :3000)
```

Apache configuration already includes:
- Trust in Cloudflare IPs to detect real client IP
- `CF-Connecting-IP` header to get original IP
- Automatic HTTP → HTTPS redirect

### 6. Admin Panel

The Admin Panel allows managing users, groups, roles, and configurations from the browser.

**Access:**
- URL: `https://admin.chat.example.com`
- Login: Use first user credentials (auto-admin)

**Features:**
- Manage users (create, edit, delete)
- Create groups and assign users
- Configure custom roles and permissions
- Edit configurations live (without restart)
- Apply role/group overrides
- Manage MCP servers

**Required configuration:**

`setup.sh` automatically generates `ADMIN_PANEL_SESSION_SECRET` in `.env`. If you already have `.env`, add manually:

```bash
# Generate with: openssl rand -hex 32
ADMIN_PANEL_SESSION_SECRET=xxxxx-64-hex-characters
```

**DNS in Cloudflare:**
- Add `admin` record type `A` or `CNAME` pointing to your server
- Enable proxy (orange cloud)

### 7. Cloudflare Turnstile (optional)

Bot protection for login and registration forms.

**Configuration:**

1. Create a widget at [Cloudflare Turnstile Dashboard](https://dash.cloudflare.com/turnstile)
2. Copy the **Site Key** (public key)
3. Edit `.env`:

```bash
TURNSTILE_SITE_KEY=0x4AAAAAAAxxxxxxxxxx
```

4. Restart LibreChat:

```bash
docker compose restart api
```

**Security limitation:**
The current LibreChat implementation only validates the token **client-side**. There is no server-side token verification. This blocks casual bots but doesn't protect against direct API attacks. For personal use with `ALLOW_REGISTRATION=false`, the risk is minimal.

## Included Services

| Service | Port | Description |
|---------|------|-------------|
| LibreChat | 3080 | Web interface + API |
| Admin Panel | 3000 | User, group, role management |
| MongoDB | - | Conversation database |
| Meilisearch | 7700 | Full-text search |
| PostgreSQL (pgvector) | - | Vector database (RAG) |
| RAG API | 8000 | Retrieval-Augmented Generation API |
| Ollama | 11434 | Local AI models |
| SearXNG | 8080 | Web search engine (meta-search) |
| Valkey | - | Cache for SearXNG |

## Configured AI Providers

| Provider | Type | Models |
|----------|------|--------|
| **Anthropic** | Cloud (API key) | Claude Sonnet, Opus, Haiku |
| **Qwen** | Cloud (API key) | Qwen Max, Plus, Turbo, VL |
| **DeepSeek** | Cloud (API key) | DeepSeek Chat, Reasoner |
| **Zhipu AI** | Cloud (API key) | GLM-4 Plus, Air, Flash |
| **Ollama** | Local | Llama, Mistral, Qwen, DeepSeek-R1 |

## Web Search

Web search uses 3 components:

| Component | Service | Description |
|-----------|---------|-------------|
| **Search** | SearXNG (local) | Meta-search engine aggregating results from Google, DuckDuckGo, etc. |
| **Scraper** | Tavily (API) | Extracts content from web pages |
| **Reranker** | Jina (API) | Reranks results by relevance |

## Image Generation

The **qwen-image-2.0-pro** model is integrated via MCP server. Users can generate and edit images by requesting it from agents.

## User Management

### Create Users (admin only)

With `ALLOW_REGISTRATION=false`, only admin can create users:

```bash
# Create user directly
docker compose exec api npm run create-user

# Invite user by email
docker compose exec api npm run invite-user user@example.com
```

### List Users

```bash
docker compose exec api npm run list-users
```

## Ollama Models

### Download Models

```bash
docker exec -it ollama ollama pull <model>
```

**Recommended models for RTX 4060 (8GB VRAM):**

- `llama3.2` (3B) - Fast and efficient
- `qwen2.5` (7B) - Good general performance
- `deepseek-r1` (7B) - Advanced reasoning
- `mistral` (7B) - Balanced
- `codellama` (7B) - Code specialized

## Maintenance

### Update Stack

```bash
git pull
git submodule update --remote --merge
docker compose pull
docker compose up -d --build
```

### Data Backup

```bash
# Backup MongoDB
docker exec chat-mongodb mongodump --out /backup
docker cp chat-mongodb:/backup ./backup-mongodb

# Backup uploads
tar -czf backup-uploads.tar.gz uploads/
```

### Logs

```bash
# View LibreChat logs
docker compose logs -f api

# View Ollama logs
docker logs -f ollama

# View SearXNG logs
docker logs -f searxng
```

## Troubleshooting

### Ollama Doesn't Detect GPU

```bash
# Verify NVIDIA Container Toolkit
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

### Permission Error

```bash
sudo chown -R 1000:1000 data-node meili_data uploads logs
```

### SearXNG Not Responding

```bash
# Verify JSON API is enabled
curl 'http://localhost:8080/search?q=test&format=json'

# Restart SearXNG
docker compose restart searxng
```

### Port 3080 Occupied

Change port in `.env`:

```bash
PORT=3081
```

And update Apache2 to point to the new port.
