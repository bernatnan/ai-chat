# Testing LibreChat Official Image

This document explains how to test the official LibreChat image with our custom services.

## Quick Start

### 1. Prepare environment

```bash
# Copy the test environment file
cp .env.test .env.test.local

# Edit and fill in your actual values
nano .env.test.local
```

**Required variables to fill:**
- `MEILI_MASTER_KEY` - any random string
- `ADMIN_PANEL_SESSION_SECRET` - any random string
- `SEARXNG_SECRET` - any random string
- API keys for providers you want to test (TAVILY_API_KEY, JINA_API_KEY, etc.)

### 2. Start services

```bash
# Start all services
docker compose -f docker-compose.test.yml --env-file .env.test.local up -d

# Check logs
docker compose -f docker-compose.test.yml logs -f api
```

### 3. Access LibreChat

- Main UI: http://localhost:3080
- Admin Panel: http://localhost:3000
- SearXNG: http://localhost:8080
- LocalAI: http://localhost:8180

### 4. Test features

1. **Web Search**: 
   - Go to Settings → Parameters
   - Enable "Web Search"
   - Try a search query

2. **TTS/STT**:
   - Go to Settings → Speech
   - Test text-to-speech and speech-to-text

3. **File Upload**:
   - Try uploading a file in a chat

4. **Image Generation**:
   - Try generating an image (if you have Qwen Image configured)

### 5. Stop services

```bash
docker compose -f docker-compose.test.yml down
```

## Troubleshooting

### Check if webSearch is in /api/config

```bash
curl -s http://localhost:3080/api/config | python3 -m json.tool | grep -A 10 "webSearch"
```

### Check LibreChat logs

```bash
docker logs LibreChat --tail 100
```

### Check SearXNG

```bash
curl "http://localhost:8080/search?q=test&format=json"
```

### Check LocalAI

```bash
curl http://localhost:8180/readyz
curl http://localhost:8180/v1/models
```

## Differences from our custom setup

This test setup uses:
- ✅ Official LibreChat image (no custom Dockerfile)
- ✅ Our librechat.yaml configuration
- ✅ Our SearXNG configuration
- ✅ Our LocalAI configuration
- ❌ No custom entrypoint script
- ❌ No custom assets volume
- ❌ No generated_files volume

If web search works here but not in our custom setup, the issue is in our Dockerfile.custom or entrypoint script.
