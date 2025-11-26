# AI Backend Configuration - Quick Reference

## Current Default: Modal (FREE)

The NACC orchestrator is configured to use **Modal** as the default AI backend.
Modal provides FREE serverless GPU infrastructure for the hackathon.

## Setup Instructions

### For Modal (Default - FREE):
```bash
# 1. Install and authenticate
pip install modal
modal token new

# 2. Start Modal in development mode
modal serve src/nacc_orchestrator/modal_backend.py

# 3. Start orchestrator (in another terminal)
nacc-orchestrator serve --config configs/orchestrator.yml
```

### For Other Backends (Requires YOUR API Keys):

#### Gemini:
```bash
export GEMINI_API_KEY="your-key-from-https://aistudio.google.com/"
# Edit configs/orchestrator.yml and change kind to "gemini"
```

#### OpenAI:
```bash
export OPENAI_API_KEY="your-key-from-https://platform.openai.com/"
# Edit configs/orchestrator.yml and change kind to "openai"
```

#### Cerebras:
```bash
export CEREBRAS_API_KEY="your-key-from-https://cloud.cerebras.ai/"
# Edit configs/orchestrator.yml and change kind to "cerebras"
```

### For Blaxel (FREE 10 Requests - No Personal API Key):

#### Blaxel OpenAI (10 free requests):
```bash
export BLAXEL_API_KEY="provided-by-nacc"
export BLAXEL_WORKSPACE="nacc-workspace"
# Edit configs/orchestrator.yml and change kind to "blaxel-openai"
```

#### Blaxel Gemini (10 free requests):
```bash
export BLAXEL_API_KEY="provided-by-nacc"
export BLAXEL_WORKSPACE="nacc-workspace"
# Edit configs/orchestrator.yml and change kind to "blaxel-gemini"
```

**Note:** Blaxel provides 10 FREE requests through their gateway.
No need for your own OpenAI or Gemini API keys - perfect for testing!

### For Local/Offline (Docker):
```bash
# No API key needed - runs locally
# Edit configs/orchestrator.yml and change kind to "docker-mistral"
docker run -d --name mistral-7b-instruct mistralai/mistral-7b-instruct-v0.2
```

## Priority Order (Recommended):

1. **modal** (default) - FREE ⭐
2. **gemini** - Your API key required 🔑
3. **openai** - Your API key required 🔑
4. **cerebras** - Your API key required 🔑
5. **blaxel-openai** - 10 free requests 🎁
6. **blaxel-gemini** - 10 free requests 🎁
7. **docker-mistral** - Local, offline 💻

## Full Documentation

See `docs/AI-BACKEND-GUIDE.md` for complete details on:
- Cost comparisons
- Performance characteristics
- Troubleshooting
- API key management
- Switching backends

## Quick Backend Switch

Edit `configs/orchestrator.yml`:
```yaml
agent_backend:
  kind: modal  # Change to: gemini, openai, cerebras, blaxel-openai, blaxel-gemini, docker-mistral
  container_id: null  # For API key backends, set to your key or use env var
```

Then restart:
```bash
nacc-orchestrator serve --config configs/orchestrator.yml
```
