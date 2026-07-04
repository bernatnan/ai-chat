# AI Chat Stack

Plataforma de xat amb IA auto-allotjada, construïda sobre [LibreChat](https://github.com/danny-avila/LibreChat) amb serveis addicionals per a cerca web, generació d'imatges i models locals.

## Característiques

- **Multi-proveïdor d'IA**: Anthropic, Qwen, DeepSeek, Zhipu AI i models locals via Ollama
- **Cerca web integrada**: SearXNG (local) + Tavily (scraper) + Jina (reranker)
- **Generació d'imatges**: Qwen Image 2.0 Pro via MCP server
- **Models locals**: Ollama amb suport GPU (NVIDIA) o CPU
- **Admin Panel**: Gestió d'usuaris, grups, rols i configuracions des del navegador
- **Gestió d'usuaris**: Registre limitat a admin, rols i permisos granulars
- **Protecció contra bots**: Cloudflare Turnstile (client-side)
- **RAG**: Retrieval-Augmented Generation amb pgvector
- **Cerca full-text**: Meilisearch per cercar en converses
- **Privacitat**: Totes les dades es guarden localment

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

## Instal·lació ràpida

```bash
# 1. Clonar el repositori
git clone https://github.com/bernatnan/ai-chat.git
cd ai-chat

# 2. Executar el setup (genera secrets i crea .env)
./setup.sh

# 3. Editar .env per configurar API keys i domini
nano .env

# 4. Crear el primer usuari admin
docker compose exec api npm run create-user

# 5. Descarregar models d'Ollama (opcional)
docker exec -it ollama ollama pull llama3.2
```

Veure [DEPLOY.md](DEPLOY.md) per a la guia completa de desplegament.

## Serveis inclosos

| Servei | Port | Descripció | Local? |
|--------|------|------------|:------:|
| LibreChat | 3080 | Interfície web + API | ✅ |
| Admin Panel | 3000 | Gestió d'usuaris, grups, rols | ✅ |
| MongoDB | - | Base de dades de converses | ✅ |
| Meilisearch | 7700 | Cerca full-text | ✅ |
| PostgreSQL (pgvector) | - | Base de dades vectorial (RAG) | ✅ |
| RAG API | 8000 | Retrieval-Augmented Generation | ✅ |
| Ollama | 11434 | Models d'IA locals | ✅ |
| SearXNG | 8080 | Motor de cerca web | ✅ |
| Valkey | - | Cache per SearXNG | ✅ |

## Proveïdors d'IA

| Proveïdor | Tipus | Models |
|-----------|-------|--------|
| **Anthropic** | Cloud (API key) | Claude Sonnet, Opus, Haiku |
| **OpenAI** | Cloud (API key) | GPT-4o, GPT-4, GPT-3.5, o1 |
| **Qwen** | Cloud (API key) | Qwen Max, Plus, Turbo, VL |
| **DeepSeek** | Cloud (API key) | DeepSeek Chat, Reasoner |
| **Zhipu AI** | Cloud (API key) | GLM-4 Plus, Air, Flash |
| **Ollama** | Local | Llama, Mistral, Qwen, DeepSeek-R1 |

## Cerca web

La cerca web utilitza 3 components:

| Component | Servei | Descripció | Local? |
|-----------|--------|------------|:------:|
| **Search** | SearXNG | Meta-cercador (Google, DuckDuckGo, etc.) | ✅ |
| **Scraper** | Tavily | Extreu contingut de pàgines web | ❌ (API) |
| **Reranker** | Jina | Reordena resultats per rellevància | ❌ (API) |

## Generació d'imatges

El model **qwen-image-2.0-pro** està integrat via MCP server. Els usuaris poden generar i editar imatges demanant-ho als agents.

## Configuració de models

### Models per defecte

Els models per defecte de cada proveïdor es configuren al `librechat.yaml`:

```yaml
endpoints:
  custom:
    - name: 'Qwen'
      models:
        default:
          - 'qwen-max'
          - 'qwen-plus'
          # ...
        fetch: true  # Descarrega models disponibles de l'API
```

### Selecció de models a la UI

- **`fetch: true`**: LibreChat descarrega la llista completa de models de l'API. Els usuaris poden seleccionar qualsevol model des de la interfície.
- **`fetch: false`**: Només es mostren els models llistats a `models.default`.

Actualment, **Qwen** i **Ollama** tenen `fetch: true`, la resta tenen `fetch: false`.

### Canviar models per defecte

Edita `librechat.yaml` i modifica la llista `models.default` del proveïdor que vulguis. Després reinicia:

```bash
docker compose restart api
```

### Per què tots els endpoints són custom?

En aquest projecte, **tots els proveïdors d'IA (incloent Anthropic i OpenAI) estan configurats com a endpoints custom**, no com a endpoints nadius de LibreChat.

**Motiu**: LibreChat té una limitació de disseny que impedeix controlar quins models veu cada grup d'usuaris quan s'utilitzen endpoints nadius. La variable `ENDPOINTS` del `.env` controla globalment quins endpoints nadius es carreguen, però no permet restringir-los per rol o grup.

En configurar tots els proveïdors com a endpoints custom:
- ✅ **Control granular**: Cada fitxer `librechat.yaml.X` defineix exactament quins models estan disponibles
- ✅ **Flexibilitat per grups**: Diferents usuaris poden tenir accés a diferents models
- ✅ **Consistència**: Tots els proveïdors es configuren de la mateixa manera
- ⚠️ **Limitació**: Es perden algunes optimitzacions natives de LibreChat per a Anthropic i OpenAI (com format de missatges específic), però la funcionalitat bàsica funciona correctament

**Estratègia de fitxers de configuració**:
- `librechat.yaml` - Configuració base sense Turnstile (versionada al git)
- `librechat.yaml.local` - Configuració base amb Turnstile (NO versionada, per al servidor)
- `librechat.yaml.basic` - Accés limitat (només Qwen Plus)
- `librechat.yaml.standard` - Accés estàndard (Qwen bàsic + DeepSeek + Ollama)
- `librechat.yaml.admin` - Accés complet (tots els proveïdors i models)

Per activar Turnstile al servidor:
```bash
cp librechat.yaml librechat.yaml.local
nano librechat.yaml.local  # Afegeix la secció turnstile amb la teva clau
```

Per canviar entre configuracions:
```bash
cp librechat.yaml.admin librechat.yaml
docker compose restart api
```

## Cloudflare Turnstile

El Cloudflare Turnstile està disponible com a protecció contra bots als formularis de login i registre.

### Configuració

Edita `librechat.yaml` i descomenta la secció Turnstile:

```yaml
turnstile:
  siteKey: "LA_TEVA_SITE_KEY"
  options:
    language: "ca"
    size: "normal"
```

### Limitació de seguretat

**Important**: La implementació actual de LibreChat només valida el token de Turnstile **client-side**. No hi ha verificació server-side del token.

**Implicacions**:
- ✅ Bloqueja bots casuals i automatització bàsica
- ❌ No protegeix contra atacs directes a l'API (un atacant pot enviar peticions sense passar pel widget)

**Recomanació**: Per a ús personal amb `ALLOW_REGISTRATION=false`, el risc és mínim. La seguretat real està en el control d'usuaris (només l'admin pot crear comptes).

## Requisits

- Docker i Docker Compose
- NVIDIA GPU amb drivers + NVIDIA Container Toolkit (opcional, per Ollama amb GPU)
- Mínim 8GB RAM (16GB recomanat)
- 50GB espai en disc
- **Nota**: Ollama funciona amb CPU (sense GPU), però el rendiment és inferior

## Roadmap

### Fase 1: Setup inicial (actual) ✅

- [x] LibreChat amb multi-proveïdor (Anthropic, Qwen, DeepSeek, Zhipu AI)
- [x] Ollama per models locals
- [x] SearXNG per cerca web local
- [x] Tavily com a scraper (API)
- [x] Jina com a reranker (API)
- [x] Qwen Image via MCP server
- [x] Registre limitat a admin
- [x] Cloudflare Turnstile (opcional)

### Fase 2: Substituir APIs per serveis locals

- [ ] **Scraper local**: Substituir Tavily per Firecrawl self-hosted
  - Requereix ~12GB RAM addicional
  - 5 contenidors nous (API, Playwright, Redis, RabbitMQ, PostgreSQL)
  - 100% local i privatiu
  
- [ ] **Reranker local**: Substituir Jina per model local
  - Model: `jinaai/jina-reranker-v3` (~600MB)
  - Servidor: HuggingFace TEI o similar
  - Requereix adapter/proxy per compatibilitat amb LibreChat
  - Funciona amb CPU (no necessita GPU)

### Fase 3: Optimització i escalabilitat

- [ ] **Redis per caching**: Afegir Redis per millorar rendiment
- [ ] **Backup automàtic**: Script de backup programat de MongoDB i uploads
- [ ] **Monitorització**: Integrar Prometheus + Grafana
- [ ] **Logs centralitzats**: ELK stack o similar
- [ ] **Multi-tenant**: Configurar grups i permisos avançats

### Fase 4: Funcionalitats avançades

- [ ] **Voice**: Speech-to-text i text-to-speech locals (Whisper, Piper)
- [ ] **Code Interpreter**: Execució de codi en sandbox
- [ ] **Agents avançats**: MCP servers addicionals, subagents
- [ ] **Fine-tuning**: Entrenar models locals amb dades pròpies
- [ ] **Federació**: Connectar amb altres instàncies (futur)

## Estructura del projecte

```
ai-chat/
├── docker-compose.yml          # Orquestra tots els serveis
├── .env.template               # Plantilla de configuració
├── librechat.yaml              # Configuració de LibreChat
├── setup.sh                    # Script d'instal·lació
├── DEPLOY.md                   # Guia de desplegament
├── README.md                   # Aquest fitxer
├── searxng/
│   └── settings.yml            # Configuració de SearXNG
├── docs/
│   └── apache2.conf.example    # Configuració Apache2
└── librechat/                  # Git submodule → fork de LibreChat
    ├── Dockerfile.custom       # Imatge amb MCP server
    ├── mcp-servers/
    │   └── qwen-image/         # MCP server per Qwen Image
    └── ...
```

## Gestió d'usuaris

Amb `ALLOW_REGISTRATION=false`, només l'admin pot crear usuaris:

```bash
# Crear usuari
docker compose exec api npm run create-user

# Convidar per email
docker compose exec api npm run invite-user usuari@exemple.com

# Llistar usuaris
docker compose exec api npm run list-users
```

## Actualitzacions

```bash
# Actualitzar el projecte i submodules
git pull
git submodule update --remote --merge
docker compose pull
docker compose up -d --build
```

## Contribucions

Aquest és un projecte personal. Si trobes errors o tens suggeriments, obre un issue.

## Llicència

- **AI Chat Stack**: MIT
- **LibreChat**: MIT (veure [librechat/LICENSE](librechat/LICENSE))
- **SearXNG**: AGPL-3.0

## Enllaços útils

- [LibreChat Docs](https://librechat.ai/docs)
- [SearXNG Docs](https://docs.searxng.org/)
- [Ollama Docs](https://github.com/ollama/ollama/tree/main/docs)
- [Tavily API](https://docs.tavily.com/)
- [Jina AI](https://jina.ai/)
