# NACC AI Backend Selection Guide

## Backend Priority & Configuration

NACC supports multiple AI backends with the following recommended priority:

### Priority Order (Best to Use)

1. **Modal** (Default) ✨ **FREE**
2. **Gemini** (Your API Key Required)
3. **OpenAI** (Your API Key Required)
4. **Cerebras** (Your API Key Required)
5. **Blaxel OpenAI** (FREE 10 requests)
6. **Blaxel Gemini** (FREE 10 requests)
7. **Docker Mistral** (Local, offline)

---

## 1. Modal (Default) - ⭐ RECOMMENDED

**Status:** FREE - Hackathon sponsor providing serverless GPU infrastructure

**Model:** IBM Granite-3.0-3B-A800M-Instruct (3.3B total, 800M active MoE)

**Setup:**
```bash
# 1. Install Modal
pip install modal

# 2. Authenticate
modal token new

# 3. For development (recommended):
modal serve src/nacc_orchestrator/modal_backend.py

# 4. Start orchestrator (in another terminal)
nacc-orchestrator serve --config configs/orchestrator.yml
```

**Configuration:**
```yaml
agent_backend:
  kind: modal
  container_id: null  # null = development mode
  timeout: 120.0
```

**Advantages:**
- ✅ FREE serverless GPU
- ✅ No API costs
- ✅ Fast inference (~2s)
- ✅ Automatic scaling
- ✅ Sub-second cold starts

---

## 2. Gemini - 🔑 YOUR API KEY REQUIRED

**Get API Key:** https://aistudio.google.com/

**Configuration:**
```yaml
agent_backend:
  kind: gemini
  container_id: YOUR_GEMINI_API_KEY  # Or set GEMINI_API_KEY env var
  timeout: 90.0
```

**Environment Variable (Alternative):**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

**Cost:** Pay-per-use (see Google AI pricing)

---

## 3. OpenAI - 🔑 YOUR API KEY REQUIRED

**Get API Key:** https://platform.openai.com/

**Configuration:**
```yaml
agent_backend:
  kind: openai
  container_id: YOUR_OPENAI_API_KEY  # Or set OPENAI_API_KEY env var
  timeout: 90.0
```

**Environment Variable (Alternative):**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

**Cost:** Pay-per-use (see OpenAI pricing)

---

## 4. Cerebras - 🔑 YOUR API KEY REQUIRED

**Get API Key:** https://cloud.cerebras.ai/

**Configuration:**
```yaml
agent_backend:
  kind: cerebras
  container_id: YOUR_CEREBRAS_API_KEY  # Or set CEREBRAS_API_KEY env var
  timeout: 60.0
```

**Environment Variable (Alternative):**
```bash
export CEREBRAS_API_KEY="your-api-key-here"
```

**Cost:** Pay-per-use (see Cerebras pricing)

---

## 5. Blaxel OpenAI - 🎁 FREE 10 REQUESTS

**Status:** FREE trial via Blaxel Model Gateway (limited to 10 requests/tasks)

**Configuration:**
```yaml
agent_backend:
  kind: blaxel-openai
  timeout: 90.0
  environment:
    model: gpt-4o-mini  # or gpt-4o, gpt-4-turbo
```

**Environment Variables Required:**
```bash
export BLAXEL_API_KEY="your-blaxel-key"
export BLAXEL_WORKSPACE="your-workspace"
```

**Limitations:**
- ⚠️ 10 requests maximum
- ⚠️ Requires Blaxel account setup
- ⚠️ Good for testing/demo only

---

## 6. Blaxel Gemini - 🎁 FREE 10 REQUESTS

**Status:** FREE trial via Blaxel Model Gateway (limited to 10 requests/tasks)

**Configuration:**
```yaml
agent_backend:
  kind: blaxel-gemini
  timeout: 90.0
  environment:
    model: gemini-2-0-flash-exp  # or gemini-1.5-pro
```

**Environment Variables Required:**
```bash
export BLAXEL_API_KEY="your-blaxel-key"
export BLAXEL_WORKSPACE="your-workspace"
```

**Limitations:**
- ⚠️ 10 requests maximum
- ⚠️ Requires Blaxel account setup
- ⚠️ Good for testing/demo only

---

## 7. Docker Mistral - 💻 LOCAL OFFLINE

**Status:** Local Docker container (no internet required)

**Configuration:**
```yaml
agent_backend:
  kind: docker-mistral
  container_id: mistral-7b-instruct
  timeout: 90.0
```

**Setup:**
```bash
# Pull and run Mistral container
docker run -d --name mistral-7b-instruct \
  -p 8080:8080 \
  mistralai/mistral-7b-instruct-v0.2
```

**Use Cases:**
- Offline development
- Air-gapped environments
- No API costs
- Full privacy

---

## Quick Start Recommendations

### For Hackathon/Demo:
1. **Use Modal** (default) - FREE and fast!
2. If Modal has issues, try **Blaxel** (10 free requests)

### For Production:
1. **Modal** (if sponsored/free tier continues)
2. **Gemini** (cost-effective, good quality)
3. **OpenAI** (premium quality, higher cost)

### For Local Development:
1. **Docker Mistral** (offline, no API keys)
2. **Modal** (if internet available)

---

## Changing Backends

Edit `configs/orchestrator.yml` and change the `agent_backend.kind` value:

```yaml
# Current backend
agent_backend:
  kind: modal  # Change this to: gemini, openai, cerebras, blaxel-openai, blaxel-gemini, docker-mistral

# Then restart orchestrator:
# nacc-orchestrator serve --config configs/orchestrator.yml
```

---

## API Key Management

### Option 1: Environment Variables (Recommended)
```bash
export GEMINI_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
export CEREBRAS_API_KEY="your-key"
export BLAXEL_API_KEY="your-key"
export BLAXEL_WORKSPACE="your-workspace"
```

### Option 2: Config File
```yaml
agent_backend:
  kind: gemini
  container_id: your-api-key-here  # Direct in config
```

### Option 3: .env File
Create `.env` file:
```
GEMINI_API_KEY=your-key
OPENAI_API_KEY=your-key
CEREBRAS_API_KEY=your-key
```

---

## Cost Comparison

| Backend | Cost | Speed | Quality | Limitations |
|---------|------|-------|---------|-------------|
| Modal | FREE ✅ | Fast ⚡ | Good 👍 | None |
| Gemini | $ | Fast ⚡ | Good 👍 | API key required |
| OpenAI | $$$ | Fast ⚡ | Excellent 🌟 | API key required |
| Cerebras | $$ | Very Fast ⚡⚡ | Good 👍 | API key required |
| Blaxel OpenAI | FREE ✅ | Fast ⚡ | Excellent 🌟 | 10 requests only |
| Blaxel Gemini | FREE ✅ | Fast ⚡ | Good 👍 | 10 requests only |
| Docker | FREE ✅ | Slow 🐢 | Decent 👌 | Requires Docker |

---

## Troubleshooting

### Modal Not Working?
```bash
# Check authentication
modal token new

# Check if app is deployed
modal deploy src/nacc_orchestrator/modal_backend.py

# Or use development mode
modal serve src/nacc_orchestrator/modal_backend.py
```

### API Key Errors?
```bash
# Check environment variables
echo $GEMINI_API_KEY
echo $OPENAI_API_KEY
echo $CEREBRAS_API_KEY

# Verify keys are valid at provider websites
```

### Blaxel Limit Reached?
```
# You've used your 10 free requests
# Switch to another backend or get Blaxel subscription
```

---

## Support

For issues or questions:
- Modal: https://modal.com/docs
- Gemini: https://ai.google.dev/docs
- OpenAI: https://platform.openai.com/docs
- Cerebras: https://docs.cerebras.ai/
- Blaxel: https://blaxel.ai/docs
