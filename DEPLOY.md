# Guia de Desplegament - AI Chat Stack

## Arquitectura

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

## Requisits del servidor

- Docker i Docker Compose instal·lats
- NVIDIA GPU amb drivers i NVIDIA Container Toolkit (per Ollama)
- Mínim 8GB RAM (16GB recomanat)
- 50GB espai en disc

## Instal·lació ràpida

```bash
# 1. Clonar el repositori
git clone https://github.com/bernatnan/ai-chat.git
cd ai-chat

# 2. Executar el setup
./setup.sh

# 3. Crear el primer usuari admin
docker compose exec api npm run create-user

# 4. Descarregar models d'Ollama (opcional)
docker exec -it ollama ollama pull llama3.2
docker exec -it ollama ollama pull qwen2.5
docker exec -it ollama ollama pull deepseek-r1
```

## Configuració detallada

### 1. Fitxer .env

El `setup.sh` crea el `.env` automàticament i genera els secrets. Edita'l per configurar:

```bash
nano .env
```

**Variables importants:**

| Variable | Descripció |
|----------|------------|
| `DOMAIN_CLIENT` / `DOMAIN_SERVER` | El teu domini públic (ex: `https://chat.exemple.com`) |
| `QWEN_API_KEY` | API key de DashScope (Alibaba Cloud) |
| `DEEPSEEK_API_KEY` | API key de DeepSeek |
| `ANTHROPIC_API_KEY` | API key d'Anthropic (o `user_provided`) |
| `ZHIPU_API_KEY` | API key de Zhipu AI |
| `TAVILY_API_KEY` | API key de Tavily (web scraping) |
| `JINA_API_KEY` | API key de Jina (reranker) |

**SMTP (opcional):**

```bash
EMAIL_HOST=smtp.exemple.com
EMAIL_PORT=587
EMAIL_ENCRYPTION=starttls
EMAIL_USERNAME=usuari@exemple.com
EMAIL_PASSWORD=contrasenya
EMAIL_FROM=noreply@exemple.com
EMAIL_FROM_NAME=LibreChat
```

### 2. Fitxer librechat.yaml

Ja creat amb la configuració base. Edita'l per personalitzar:

```bash
nano librechat.yaml
```

**Cloudflare Turnstile (opcional):**

```yaml
turnstile:
  siteKey: "LA_TEVA_SITE_KEY"
  options:
    language: "ca"
    size: "normal"
```

### 3. Apache2 Reverse Proxy amb SSL

```bash
# Instal·lar mòduls necessaris (inclou ssl i remoteip per Cloudflare)
sudo a2enmod proxy proxy_http proxy_wstunnel rewrite headers ssl remoteip
sudo systemctl restart apache2

# Copiar configuració
sudo cp docs/apache2.conf.example /etc/apache2/sites-available/ai-chat.conf
sudo nano /etc/apache2/sites-available/ai-chat.conf
# Edita ServerName i les rutes dels certificats SSL

# Activar i recarregar
sudo a2ensite ai-chat
sudo systemctl reload apache2
```

**Important:** 
- Al `.env`, configura `TRUST_PROXY=1` i els dominis amb `https://`
- La configuració d'Apache ja inclou redirect HTTP → HTTPS i suport per Cloudflare proxy

### 4. SSL amb Let's Encrypt

Si encara no tens el certificat:

```bash
sudo apt install certbot python3-certbot-apache
sudo certbot --apache -d chat.exemple.com
```

### 5. Configuració de Cloudflare

Si uses Cloudflare com a proxy DNS (recomanat):

1. **DNS**: Activa el proxy (icona taronja) per `chat.example.com` i `admin.chat.example.com`
2. **SSL/TLS**: Configura el mode a **"Full (Strict)"** per màxima seguretat
3. **Page Rules**: Afegeix una regla "Always Use HTTPS"
4. **Network**: Assegura't que "WebSockets" està activat

**Flux de connexió amb Cloudflare:**
```
Client → Cloudflare (HTTPS) → Apache (HTTPS) → LibreChat (HTTP :3080)
Client → Cloudflare (HTTPS) → Apache (HTTPS) → Admin Panel (HTTP :3000)
```

La configuració d'Apache ja inclou:
- Trust en les IPs de Cloudflare per detectar la IP real del client
- Header `CF-Connecting-IP` per obtenir la IP original
- Redirect automàtic HTTP → HTTPS

### 6. Admin Panel

L'Admin Panel permet gestionar usuaris, grups, rols i configuracions des del navegador.

**Accés:**
- URL: `https://admin.chat.example.com`
- Login: Usa les credencials del primer usuari (és auto-admin)

**Funcionalitats:**
- Gestionar usuaris (crear, editar, eliminar)
- Crear grups i assignar usuaris
- Configurar rols i permisos personalitzats
- Editar configuracions en viu (sense reiniciar)
- Aplicar overrides per rol/grup
- Gestionar MCP servers

**Configuració necessària:**

El `setup.sh` genera automàticament `ADMIN_PANEL_SESSION_SECRET` al `.env`. Si ja tens el `.env`, afegeix manualment:

```bash
# Genera amb: openssl rand -hex 32
ADMIN_PANEL_SESSION_SECRET=xxxxx-64-caracters-hex
```

**DNS a Cloudflare:**
- Afegeix un registre `admin` tipus `A` o `CNAME` apuntant al teu servidor
- Activa el proxy (icona taronja)

### 7. Cloudflare Turnstile (opcional)

Protecció contra bots als formularis de login i registre.

**Configuració:**

1. Crea un widget a [Cloudflare Turnstile Dashboard](https://dash.cloudflare.com/turnstile)
2. Copia la **Site Key** (clau pública)
3. Edita el `.env`:

```bash
TURNSTILE_SITE_KEY=0x4AAAAAAAxxxxxxxxxx
```

4. Reinicia LibreChat:

```bash
docker compose restart api
```

**Limitació de seguretat:**
La implementació actual de LibreChat només valida el token **client-side**. No hi ha verificació server-side del token. Això bloqueja bots casuals però no protegeix contra atacs directes a l'API. Per a ús personal amb `ALLOW_REGISTRATION=false`, el risc és mínim.

## Serveis inclosos

| Servei | Port | Descripció |
|--------|------|------------|
| LibreChat | 3080 | Interfície web + API |
| Admin Panel | 3000 | Gestió d'usuaris, grups, rols |
| MongoDB | - | Base de dades de converses |
| Meilisearch | 7700 | Cerca full-text |
| PostgreSQL (pgvector) | - | Base de dades vectorial (RAG) |
| RAG API | 8000 | API per Retrieval-Augmented Generation |
| Ollama | 11434 | Models d'IA locals |
| SearXNG | 8080 | Motor de cerca web (meta-search) |
| Valkey | - | Cache per SearXNG |

## Proveïdors d'IA configurats

| Proveïdor | Tipus | Models |
|-----------|-------|--------|
| **Anthropic** | Cloud (API key) | Claude Sonnet, Opus, Haiku |
| **Qwen** | Cloud (API key) | Qwen Max, Plus, Turbo, VL |
| **DeepSeek** | Cloud (API key) | DeepSeek Chat, Reasoner |
| **Zhipu AI** | Cloud (API key) | GLM-4 Plus, Air, Flash |
| **Ollama** | Local | Llama, Mistral, Qwen, DeepSeek-R1 |

## Cerca web

La cerca web utilitza 3 components:

| Component | Servei | Descripció |
|-----------|--------|------------|
| **Search** | SearXNG (local) | Meta-cercador que agrega resultats de Google, DuckDuckGo, etc. |
| **Scraper** | Tavily (API) | Extreu el contingut de les pàgines web |
| **Reranker** | Jina (API) | Reordena resultats per rellevància |

## Generació d'imatges

El model **qwen-image-2.0-pro** està integrat via MCP server. Els usuaris poden generar i editar imatges demanant-ho als agents.

## Gestió d'usuaris

### Crear usuaris (només admin)

Amb `ALLOW_REGISTRATION=false`, només l'admin pot crear usuaris:

```bash
# Crear usuari directament
docker compose exec api npm run create-user

# Convidar usuari per email
docker compose exec api npm run invite-user usuari@exemple.com
```

### Llistar usuaris

```bash
docker compose exec api npm run list-users
```

## Models d'Ollama

### Descarregar models

```bash
docker exec -it ollama ollama pull <model>
```

**Models recomanats per RTX 4060 (8GB VRAM):**

- `llama3.2` (3B) - Ràpid i eficient
- `qwen2.5` (7B) - Bon rendiment general
- `deepseek-r1` (7B) - Raonament avançat
- `mistral` (7B) - Equilibrat
- `codellama` (7B) - Especialitzat en codi

## Manteniment

### Actualitzar el stack

```bash
git pull
git submodule update --remote --merge
docker compose pull
docker compose up -d --build
```

### Backup de dades

```bash
# Backup MongoDB
docker exec chat-mongodb mongodump --out /backup
docker cp chat-mongodb:/backup ./backup-mongodb

# Backup uploads
tar -czf backup-uploads.tar.gz uploads/
```

### Logs

```bash
# Veure logs de LibreChat
docker compose logs -f api

# Veure logs d'Ollama
docker logs -f ollama

# Veure logs de SearXNG
docker logs -f searxng
```

## Troubleshooting

### Ollama no detecta la GPU

```bash
# Verificar NVIDIA Container Toolkit
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

### Error de permisos

```bash
sudo chown -R 1000:1000 data-node meili_data uploads logs
```

### SearXNG no respon

```bash
# Verificar que el JSON API està habilitat
curl 'http://localhost:8080/search?q=test&format=json'

# Reiniciar SearXNG
docker compose restart searxng
```

### Port 3080 ocupat

Canvia el port al `.env`:

```bash
PORT=3081
```

I actualitza Apache2 per apuntar al nou port.
