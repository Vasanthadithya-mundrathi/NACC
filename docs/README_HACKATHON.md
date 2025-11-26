# NACC - Network Agentic Connection Call
## MCP Birthday Hackathon Submission

**NACC** is an AI-powered multi-node orchestration platform that allows you to manage, execute commands, and transfer files across a distributed network of nodes using natural language.

### 🚀 Key Features
- **Multi-Node Orchestration**: Manage local Mac/Linux machines and remote VMs (e.g., Kali Linux).
- **AI-Powered**: Uses advanced LLMs (OpenAI, Gemini, Mistral, Blaxel) to understand intent and route commands.
- **Node Management**: Securely pair new nodes with a 6-digit code.
- **File System Access**: Browse, read, and write files across the network.
- **Modern UI**: Dark-themed, responsive interface with real-time dashboard.

### 🛠️ Installation

1. **Clone the repository**
2. **Run the setup script**:
   ```bash
   ./install.sh
   ```

### 🏃‍♂️ Running NACC

Start the full system (Orchestrator + UI):
```bash
./start_nacc.sh
```

Or run components individually:
```bash
# Start Orchestrator
nacc-orchestrator serve

# Start UI
nacc-ui
```

### 🔗 Node Pairing (New Feature!)

To add a new node (e.g., a Kali VM):

1. **On the Node**:
   ```bash
   nacc-node init
   ```
   *This will generate a 6-digit pairing code.*

2. **On the Orchestrator**:
   ```bash
   nacc-orchestrator register-node <CODE> --ip <NODE_IP>
   ```

### 🧪 Testing

The project includes a comprehensive test suite.
```bash
pytest
```

### 🤖 AI Backends

NACC supports multiple backends. The default is **Blaxel Sandbox (OpenAI)** for this hackathon.
You can switch backends in the UI or via `configs/orchestrator.yml`.

---
*Built for the MCP Birthday Hackathon 2025*
