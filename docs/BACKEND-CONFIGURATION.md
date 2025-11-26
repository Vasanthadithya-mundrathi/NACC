# NACC Backend Configuration Guide

## Overview

NACC supports **three AI backend options** to give developers flexibility based on their requirements:

1. **Docker Mistral** - Local, privacy-focused
2. **Cerebras API** - Cloud, highest accuracy
3. **Blaxel Gateway** - Multi-provider cloud gateway

## Backend Comparison

| Backend | Privacy | Cost | Accuracy | Speed | Best For |
|---------|---------|------|----------|-------|----------|
| **Docker Mistral** | ✅ Local | ✅ Free | 80% | Medium | Privacy-sensitive, offline work |
| **Cerebras API** | ⚠️ Cloud | 💰 Paid | 100% | ⚠️ Fast | Production, high accuracy needs |
| **Blaxel Gateway** | ⚠️ Cloud | 💰 Paid | High | ⚠️ Fast | Multi-model flexibility, monitoring |

## Configuration

### 1. Docker Mistral (Local)

**Use Case**: Privacy-focused development, no API costs, offline work

**Setup**:
```bash
# Pull Mistral model
docker pull docker.io/ollama/ollama:latest
docker run -d --name mistral-llm -p 11434:11434 ollama/ollama
docker exec mistral-llm ollama pull mistral-nemo
```

**Environment Variables**:
```bash
export NACC_DOCKER_LLM_CONTAINER="mistral-llm"
```

**Config Example**:
```yaml
agent_backend:
  kind: docker-mistral
  container_id: mistral-llm
  command:
    - docker
    - exec
    - mistral-llm
    - ollama
    - run
    - mistral-nemo
  timeout: 30
  environment:
    model: mistral-nemo
```

**Pros**:
- ✅ Completely local - no data leaves your machine
- ✅ No API costs
- ✅ Works offline
- ✅ Full control over model

**Cons**:
- ❌ Requires Docker and disk space (~8GB)
- ❌ Lower accuracy (80% in tests)
- ❌ Slower than cloud APIs
- ❌ Limited to available Ollama models

---

### 2. Cerebras API (Cloud)

**Use Case**: Production deployments, highest accuracy requirements

**Setup**:
```bash
# Get API key from https://cloud.cerebras.ai/
export CEREBRAS_API_KEY="your-api-key-here"
```

**Environment Variables**:
```bash
export CEREBRAS_API_KEY="csk-xxxxx"
```

**Config Example**:
```yaml
agent_backend:
  kind: cerebras
  container_id: ${CEREBRAS_API_KEY}  # or hardcode key
  environment:
    model: zai-glm-4.6  # Recommended: 100% accuracy in tests
```

**Available Models**:
- `zai-glm-4.6` - **Recommended** (100% test accuracy)
- `llama3.1-8b` - Faster, slightly lower accuracy
- `llama3.1-70b` - Highest capability

**Pros**:
- ✅ Highest accuracy (100% in tests)
- ✅ Very fast inference
- ✅ No local resources needed
- ✅ Multiple model options

**Cons**:
- ❌ Requires API key and internet
- ❌ Costs money (pay per token)
- ❌ Data sent to cloud
- ❌ Subject to rate limits

---

### 3. Blaxel Gateway (Multi-Provider Cloud)

**Use Case**: Unified access to multiple models, built-in monitoring, cost control

**Setup**:
```bash
# Get credentials from https://blaxel.ai/
export BLAXEL_API_KEY="bl_xxxxx"
export BLAXEL_WORKSPACE="your-workspace-name"
```

**Environment Variables**:
```bash
export BLAXEL_API_KEY="bl_aaab2v2ljj61gumirbwukm9deyva37sq"
export BLAXEL_WORKSPACE="vasanthfeb13"
```

**Config Example (OpenAI Models)**:
```yaml
agent_backend:
  kind: blaxel-openai  # or just "blaxel"
  container_id: ${BLAXEL_API_KEY}
  environment:
    workspace: vasanthfeb13
    model: gpt-4o-mini  # or gpt-4o, gpt-4-turbo
```

**Config Example (Gemini Models)**:
```yaml
agent_backend:
  kind: blaxel-gemini
  container_id: ${BLAXEL_API_KEY}
  environment:
    workspace: vasanthfeb13
    model: gemini-1.5-flash  # or gemini-1.5-pro
```

**Available Models**:

*OpenAI (Tested ✅)*:
- `gpt-4o-mini` - **Recommended** (fast, cost-effective, tested working)
- `gpt-4o` - Most capable GPT-4
- `gpt-4-turbo` - Fast GPT-4

*Gemini (Experimental)*:
- `gemini-1.5-flash` - Fast, multimodal
- `gemini-1.5-pro` - Most capable Gemini

**Pros**:
- ✅ Unified API for multiple providers
- ✅ Built-in telemetry and monitoring
- ✅ Cost control and fallbacks
- ✅ Switch models without code changes
- ✅ Excellent structured output (tested with GPT-4o-mini)

**Cons**:
- ❌ Requires API key and internet
- ❌ Costs money (varies by model)
- ❌ Data sent to cloud
- ❌ Gemini models may have availability issues

---

## Testing Results

From `TESTING-RESULTS.md`:

### Docker Mistral
- **Overall Success Rate**: 80%
- **Tool Identification Accuracy**: 80%
- Best for: Basic file operations, simple commands

### Cerebras (zai-glm-4.6)
- **Overall Success Rate**: 100%
- **Tool Identification Accuracy**: 100%
- Best for: Complex tool selection, production use

### Blaxel (gpt-4o-mini)
- **Status**: Tested and working ✅
- **Structured Output**: Perfect JSON format
- **Accuracy**: Expected high (similar to OpenAI)

---

## Quick Start Examples

### Local Privacy-First Setup
```bash
# Start Docker Mistral
docker run -d --name mistral-llm -p 11434:11434 ollama/ollama
docker exec mistral-llm ollama pull mistral-nemo

# Configure NACC
export NACC_DOCKER_LLM_CONTAINER="mistral-llm"

# Run orchestrator (will use Docker Mistral by default)
python src/nacc_orchestrator/orchestrator.py
```

### High-Accuracy Cloud Setup
```bash
# Configure Cerebras
export CEREBRAS_API_KEY="your-key"

# Update config to use Cerebras backend
# Edit your config YAML to use kind: cerebras

# Run orchestrator
python src/nacc_orchestrator/orchestrator.py
```

### Multi-Model Gateway Setup
```bash
# Configure Blaxel
export BLAXEL_API_KEY="bl_xxxxx"
export BLAXEL_WORKSPACE="your-workspace"

# Update config to use Blaxel backend
# Edit your config YAML to use kind: blaxel-openai

# Run orchestrator
python src/nacc_orchestrator/orchestrator.py
```

---

## Switching Backends

You can switch backends by modifying your orchestrator config:

```yaml
# config.yaml
nodes:
  - name: mac
    uri: ws://localhost:8765
    agent_backend:
      kind: cerebras  # Change this: docker-mistral, cerebras, blaxel-openai, blaxel-gemini
      container_id: ${CEREBRAS_API_KEY}
      environment:
        model: zai-glm-4.6
```

Or use environment variables:
```bash
# Switch to Cerebras
export NACC_BACKEND_KIND="cerebras"
export CEREBRAS_API_KEY="your-key"

# Switch to Blaxel
export NACC_BACKEND_KIND="blaxel-openai"
export BLAXEL_API_KEY="your-key"
export BLAXEL_WORKSPACE="your-workspace"
```

---

## Recommendations

**For Development**:
- Start with **Docker Mistral** (free, private)
- If accuracy issues → upgrade to **Cerebras** or **Blaxel**

**For Production**:
- Use **Cerebras** (proven 100% accuracy)
- Or **Blaxel** for multi-model flexibility and monitoring

**For Privacy-Sensitive**:
- Use **Docker Mistral** only (fully local)

**For Cost Optimization**:
- **Docker Mistral**: Free but requires compute resources
- **Blaxel GPT-4o-mini**: Low cost per token
- **Cerebras**: Competitive pricing with high performance

---

## Troubleshooting

### Docker Mistral Issues
```bash
# Check container status
docker ps | grep mistral-llm

# Check logs
docker logs mistral-llm

# Restart container
docker restart mistral-llm
```

### Cerebras API Issues
```bash
# Test API key
curl https://api.cerebras.ai/v1/chat/completions \
  -H "Authorization: Bearer $CEREBRAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"zai-glm-4.6","messages":[{"role":"user","content":"test"}]}'
```

### Blaxel Gateway Issues
```bash
# Test OpenAI endpoint
curl "https://run.blaxel.ai/$BLAXEL_WORKSPACE/openai/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "X-Blaxel-Workspace: $BLAXEL_WORKSPACE" \
  -H "X-Blaxel-Authorization: Bearer $BLAXEL_API_KEY" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"test"}]}'
```

---

## API Keys & Security

**Never commit API keys to version control!**

Use environment variables or `.env` files:

```bash
# .env (add to .gitignore!)
CEREBRAS_API_KEY=csk-xxxxx
BLAXEL_API_KEY=bl_xxxxx
BLAXEL_WORKSPACE=your-workspace
```

Then load in your code:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## Next Steps

1. Choose your backend based on requirements
2. Set up credentials (if using cloud APIs)
3. Update your orchestrator config
4. Test with: `python src/nacc_orchestrator/orchestrator.py`
5. Monitor accuracy and switch if needed

For detailed testing results, see `TESTING-RESULTS.md`.
