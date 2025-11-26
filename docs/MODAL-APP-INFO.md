# Modal Backend - App Information

## NACC Modal Application

**App Name:** `nacc-granite-moe-3b`  
**App ID:** `ap-8PaCvfA0O7brdDuCMSuNRV` (DEPLOYED)  
**Dashboard:** https://modal.com/apps/vasanthfeb13/main/ap-8PaCvfA0O7brdDuCMSuNRV

## Model Information

**Model:** IBM Granite-3.0-3B-A800M-Instruct  
**HuggingFace:** `ibm-granite/granite-3.0-3b-a800m-instruct`  
**Architecture:** Mixture of Experts (MoE)  
**Parameters:** 3.3B total, 800M active  
**Experts:** 32 experts with TopK=8 routing  
**License:** Apache 2.0

## GPU Configuration

**GPU Type:** A10G  
**Timeout:** 600 seconds (10 minutes)  
**Scaledown Window:** 120 seconds  

## Functions

### `generate_completion`
- **Type:** Modal Function
- **Method:** POST
- **Input:** `{"prompt": str, "context": dict}`
- **Output:** `{"response": str}`

## Usage

### Development Mode (Local):
```bash
# Terminal 1: Start Modal serve
modal serve src/nacc_orchestrator/modal_backend.py

# Terminal 2: Start Orchestrator
nacc-orchestrator serve --config configs/orchestrator.yml
```

### Production Mode (Deployed):
```bash
# Deploy once
modal deploy src/nacc_orchestrator/modal_backend.py

# Get endpoint URL and set in config
# Update orchestrator.yml: container_id: <endpoint-url>
```

## Testing

### Test Modal Function Directly:
```bash
modal run src/nacc_orchestrator/modal_backend.py
```

### Test via Orchestrator:
```bash
curl -X POST http://localhost:8888/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "write hello world to test.txt",
    "current_node": "macbook-local"
  }'
```

## Performance

**Cold Start:** ~10-15 seconds (first request, model download)  
**Warm Inference:** ~2 seconds (cached model)  
**Accuracy:** 100% on NACC test queries  

## Cost

**Status:** FREE  
**Provider:** Modal (Hackathon Sponsor)  
**Billing:** Serverless, no charges during hackathon

## Monitoring

View real-time logs and metrics:  
https://modal.com/apps/vasanthfeb13/main/ap-PDssJOi9kVAgrY4gyzgsLD

## Notes

- This app is deployed and ready to use
- No re-deployment needed unless code changes
- The app ID is fixed and documented in configs
- Use `modal serve` for development with hot-reload
- Use deployed endpoint for production
