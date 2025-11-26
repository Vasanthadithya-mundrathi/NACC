# ✅ NACC Setup Checklist

Use this checklist to ensure NACC is properly set up and running.

## Prerequisites

- [ ] Python 3.10+ installed
- [ ] Git repository cloned
- [ ] Terminal access

## Installation Steps

### 1. Environment Setup
- [ ] Created virtual environment: `python3 -m venv .venv`
- [ ] Activated venv: `source .venv/bin/activate`
- [ ] Installed dependencies: `pip install -e .`
- [ ] Verified installation: `nacc-orchestrator --help`

### 2. Modal Backend Setup (Default - FREE)
- [ ] Installed Modal: `pip install modal`
- [ ] Authenticated: `modal token new`
- [ ] Tested Modal: `modal --help`
- [ ] Verified auth: `modal token current`

### 3. Alternative: Other Backend Setup (Optional)

Choose ONE if not using Modal:

**Gemini:**
- [ ] Got API key from https://aistudio.google.com/
- [ ] Set env var: `export GEMINI_API_KEY="your-key"`
- [ ] Updated config: Set `kind: gemini` in `orchestrator.yml`

**OpenAI:**
- [ ] Got API key from https://platform.openai.com/
- [ ] Set env var: `export OPENAI_API_KEY="your-key"`
- [ ] Updated config: Set `kind: openai` in `orchestrator.yml`

**Cerebras:**
- [ ] Got API key from https://cloud.cerebras.ai/
- [ ] Set env var: `export CEREBRAS_API_KEY="your-key"`
- [ ] Updated config: Set `kind: cerebras` in `orchestrator.yml`

**Blaxel (10 free requests):**
- [ ] Set env vars: `BLAXEL_API_KEY` and `BLAXEL_WORKSPACE`
- [ ] Updated config: Set `kind: blaxel-openai` or `blaxel-gemini`

**Docker (Local/Offline):**
- [ ] Docker installed and running
- [ ] Pulled Mistral image
- [ ] Updated config: Set `kind: docker-mistral`

## Running NACC

### Option A: Automated Startup (Recommended)
- [ ] Made script executable: `chmod +x start_nacc.sh`
- [ ] Run: `./start_nacc.sh`
- [ ] Verify all services started successfully
- [ ] Check logs in `logs/` directory

### Option B: Manual Startup

**Terminal 1 - Modal Backend (if using Modal):**
- [ ] `source .venv/bin/activate`
- [ ] `modal serve src/nacc_orchestrator/modal_backend.py`
- [ ] Wait for "Running app..." message

**Terminal 2 - Orchestrator:**
- [ ] `source .venv/bin/activate`
- [ ] `nacc-orchestrator serve --config configs/orchestrator.yml`
- [ ] Wait for "Uvicorn running on http://0.0.0.0:8888"

**Terminal 3 - UI:**
- [ ] `source .venv/bin/activate`
- [ ] `nacc-ui --config configs/ui-modal.yml --share`
- [ ] Note the local and public URLs

## Verification

### Health Checks
- [ ] Orchestrator health: `curl http://localhost:8888/health`
- [ ] UI accessible at http://localhost:7860
- [ ] Modal backend responding (if using Modal)

### Functional Tests

**Test 1: Write File**
- [ ] In UI, enter: "write hello world to test.txt"
- [ ] Verify success message
- [ ] Check file created: `ls -la /tmp/nacc-local/`

**Test 2: Read File**
- [ ] In UI, enter: "read file test.txt"
- [ ] Verify content shows "hello world"

**Test 3: Execute Command**
- [ ] In UI, enter: "execute ls -la command"
- [ ] Verify directory listing appears

**Test 4: List Files**
- [ ] In UI, enter: "list all files"
- [ ] Verify file list appears

### API Test (Optional)
- [ ] Test with curl:
```bash
curl -X POST http://localhost:8888/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "write test to file.txt", "current_node": "macbook-local"}'
```
- [ ] Verify JSON response received

## Troubleshooting

### If Modal fails:
- [ ] Check authentication: `modal token current`
- [ ] Re-authenticate: `modal token new`
- [ ] Check Modal is running: `ps aux | grep modal`
- [ ] Check logs: `cat logs/modal.log`

### If Orchestrator fails:
- [ ] Check port 8888 not in use: `lsof -i :8888`
- [ ] Check config file exists: `ls -la configs/orchestrator.yml`
- [ ] Check logs: `cat logs/orchestrator.log`
- [ ] Verify backend config in orchestrator.yml

### If UI fails:
- [ ] Check port 7860 not in use: `lsof -i :7860`
- [ ] Check orchestrator is running
- [ ] Check logs: `cat logs/ui.log`
- [ ] Verify ui-modal.yml has correct orchestrator URL

### General Issues:
- [ ] Check all terminals are using activated venv
- [ ] Check all dependencies installed: `pip list`
- [ ] Check Python version: `python --version` (must be 3.10+)
- [ ] Restart all services: `pkill -f nacc && ./start_nacc.sh`

## Configuration Review

### Orchestrator Config (`configs/orchestrator.yml`)
- [ ] `agent_backend.kind` set correctly
- [ ] API key or endpoint configured (if not using Modal)
- [ ] Nodes configured (at least macbook-local)
- [ ] Timeout values appropriate

### UI Config (`configs/ui-modal.yml`)
- [ ] `orchestrator_url` points to http://127.0.0.1:8888
- [ ] Port is 7860
- [ ] Refresh interval is reasonable (5-10 seconds)

## Documentation Review

- [ ] Read: `AI-BACKEND-SETUP.md`
- [ ] Read: `docs/AI-BACKEND-GUIDE.md`
- [ ] Read: `PROJECT-UPDATE-SUMMARY.md`
- [ ] Review example configs in `configs/`

## Production Readiness (Optional)

### For Production Deployment:
- [ ] Deploy Modal app: `modal deploy src/nacc_orchestrator/modal_backend.py`
- [ ] Set `MODAL_ENDPOINT_URL` environment variable
- [ ] Update `container_id` in orchestrator.yml with endpoint URL
- [ ] Test with production endpoint
- [ ] Set up monitoring/logging
- [ ] Configure firewall rules
- [ ] Set up SSL/TLS if exposing publicly

## Success Criteria

✅ All checkboxes above are checked
✅ UI loads without errors
✅ Can write files via natural language
✅ Can read files via natural language
✅ Can execute commands via natural language
✅ AI backend responds within reasonable time
✅ Logs show no critical errors

## Need Help?

- 📖 Documentation: See `docs/` directory
- 🐛 Issues: Check logs in `logs/` directory
- 💡 Examples: See example configs in `configs/`
- 🔧 Troubleshooting: See `docs/AI-BACKEND-GUIDE.md`

---

**Status:** ⬜ Not Started | 🟡 In Progress | ✅ Complete

Mark your progress as you go!
