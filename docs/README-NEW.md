# NACC (Network Agentic Connection Call)

AI-powered multi-node network orchestration system with intelligent command routing and real-time monitoring.

## 🚀 Features

- 🤖 **AI-Powered Intent Detection** - Natural language commands with multiple AI backend options
- 🖥️ **Multi-Node Orchestration** - Control Mac, Kali, Linux nodes from single interface
- 📊 **Real-time Monitoring** - Live dashboard with node health and system metrics
- 🔄 **Dynamic Node Switching** - Seamlessly switch between nodes during operations
- 📁 **File Operations** - Create, read, transfer files across nodes
- 📦 **Package Management** - Install packages (brew, apt, pip) via natural language
- ⚡ **Command Execution** - Execute commands with full output capture

## Quick Start

### 1. Setup Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### 2. Setup AI Backend (Modal - Default & FREE)

```bash
# Install and authenticate Modal
pip install modal
modal token new

# Start Modal in development mode (keep this running)
modal serve src/nacc_orchestrator/modal_backend.py
```

**Note:** Modal is FREE and uses IBM Granite-3.0-3B-A800M (MoE) model on serverless GPU.

See [AI-BACKEND-SETUP.md](AI-BACKEND-SETUP.md) for other backend options (Gemini, OpenAI, Cerebras, etc.)

### 3. Start Orchestrator (in a new terminal)

```bash
source .venv/bin/activate
nacc-orchestrator serve --config configs/orchestrator.yml
```

The orchestrator will start on `http://0.0.0.0:8888`

### 4. Launch UI (in another terminal)

```bash
source .venv/bin/activate
nacc-ui --config configs/ui-modal.yml --share
```

Access the dashboard at the URL shown (local or public Gradio link)

## Architecture

```
┌──────────────────────────────────────────┐
│     Gradio UI (Port 7860)                │
│  Natural Language Interface + Dashboard  │
└─────────────────┬────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────┐
│   Orchestrator (Port 8888)               │
│  • AI Backend (Modal/Gemini/OpenAI/etc)  │
│  • Node Registry & Health Monitoring     │
│  • Command Routing & Execution           │
└──────┬───────────────┬───────────────────┘
       │               │
       ▼               ▼
┌─────────────┐  ┌─────────────┐
│  Mac Node   │  │  Kali Node  │
│  (Local)    │  │  (HTTP/SSH) │
└─────────────┘  └─────────────┘
```

## AI Backend Options

NACC supports multiple AI backends with the following priority:

1. **Modal** (Default) - FREE serverless GPU with IBM Granite MoE ⭐
2. **Gemini** - Your API key required
3. **OpenAI** - Your API key required
4. **Cerebras** - Your API key required
5. **Blaxel OpenAI** - 10 FREE requests via Blaxel gateway
6. **Blaxel Gemini** - 10 FREE requests via Blaxel gateway
7. **Docker Mistral** - Local/offline development

To change backends, edit `configs/orchestrator.yml` and change `agent_backend.kind`.

See [docs/AI-BACKEND-GUIDE.md](docs/AI-BACKEND-GUIDE.md) for full details.

## Example Commands

Once the UI is running, try these natural language commands:

```
"write hello world to test.txt"
"read file test.txt"
"execute ls -la command"
"switch to kali node"
"list all files in current directory"
"install python package requests"
```

## Testing

```bash
# Run unit tests
pytest tests/

# Test AI backend integration
python tests/test_ai_backends.py

# Test orchestrator
curl -X POST http://localhost:8888/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "read file test.txt", "current_node": "macbook-local"}'
```

## Configuration

### Main Configuration Files

- `configs/orchestrator.yml` - Default orchestrator config with Modal backend
- `configs/orchestrator-modal.yml` - Modal-specific configuration
- `configs/ui-modal.yml` - UI configuration
- `configs/node-laptop.yml` - Local node configuration
- `configs/node-kali-vm.yml` - Kali VM node configuration

### Environment Variables

```bash
# For Gemini backend
export GEMINI_API_KEY="your-key"

# For OpenAI backend
export OPENAI_API_KEY="your-key"

# For Cerebras backend
export CEREBRAS_API_KEY="your-key"

# For Blaxel backends
export BLAXEL_API_KEY="your-key"
export BLAXEL_WORKSPACE="your-workspace"
```

## Documentation

- [AI Backend Guide](docs/AI-BACKEND-GUIDE.md) - Complete guide to all AI backends
- [AI Backend Setup](AI-BACKEND-SETUP.md) - Quick setup reference
- [Quick Reference](NACC-Quick-Reference.md) - Command reference
- [VM Setup Guide](VM-SETUP-GUIDE.md) - Setting up Kali/Linux VMs
- [Conversational UI](docs/CONVERSATIONAL-UI.md) - UI documentation

## Project Structure

```
.
├── configs/              # Configuration files
├── src/
│   ├── nacc_node/       # Node server implementation
│   ├── nacc_orchestrator/  # Orchestrator and AI backends
│   │   ├── modal_backend.py
│   │   ├── cerebras_backend.py
│   │   ├── blaxel_backend.py
│   │   └── gemini_backend.py
│   └── nacc_ui/         # Gradio UI
├── scripts/             # Helper scripts
├── tests/              # Unit tests
└── docs/               # Documentation
```

## Troubleshooting

### Modal Not Working?

```bash
# Check Modal authentication
modal token new

# Verify modal serve is running
ps aux | grep "modal serve"

# Check logs
tail -f orchestrator.log
```

### Orchestrator Won't Start?

```bash
# Check if port 8888 is already in use
lsof -i :8888

# Kill existing process
pkill -f "nacc-orchestrator"

# Restart
nacc-orchestrator serve --config configs/orchestrator.yml
```

### UI Not Connecting?

Make sure the orchestrator is running on port 8888 before starting the UI.

```bash
# Check orchestrator is running
curl http://localhost:8888/health
```

## Development

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_orchestrator.py -v

# With coverage
pytest tests/ --cov=src/nacc_orchestrator --cov-report=html
```

### Adding a New AI Backend

1. Create `src/nacc_orchestrator/your_backend.py`
2. Implement `YourBackend` class with `complete()` method
3. Add to `agents.py` in `build_backend()` function
4. Add to `config.py` in `AgentBackendConfig.kind` Literal
5. Create example config in `configs/orchestrator-your.yml`

## Hackathon Achievements

- ✅ Modal serverless GPU integration (FREE!)
- ✅ IBM Granite-3.0-3B-A800M MoE model (100% accuracy on tests)
- ✅ Multiple AI backend support (6 options)
- ✅ Real Kali Linux VM orchestration
- ✅ Gradio UI with natural language interface
- ✅ MCP protocol implementation
- ✅ Multi-node file operations and command execution

## License

MIT License - See LICENSE file for details

## Acknowledgments

- **Modal** - Hackathon sponsor providing serverless GPU infrastructure
- **IBM Granite** - Open source MoE model (Apache 2.0)
- **Anthropic MCP** - Model Context Protocol
- **Gradio** - UI framework

## Support

For issues or questions:
- Check [AI-BACKEND-SETUP.md](AI-BACKEND-SETUP.md)
- See [docs/AI-BACKEND-GUIDE.md](docs/AI-BACKEND-GUIDE.md)
- Review configuration examples in `configs/`
