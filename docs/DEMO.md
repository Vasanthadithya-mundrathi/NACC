# NACC Live Demo Script

## Setup (5 minutes before demo)

1. **Start Kali VM node** (if not already running):
   ```bash
   ssh vasanth@192.168.64.2
   cd ~/nacc
   source .venv/bin/activate
   nacc-node serve --config node-config.yml --host 0.0.0.0 --port 8765
   ```

2. **Activate local environment**:
   ```bash
   cd ~/Documents/Projects/MCP\ birthday\ hackathon
   source .venv/bin/activate
   ```

3. **Verify Docker AI**:
   ```bash
   docker model status
   # Should show: Docker Model Runner is running
   ```

---

## Demo Part 1: The Problem We Solve (1 minute)

**Say**: "Imagine you have multiple machines - VMs, servers, laptops - and you want to execute tasks across them intelligently. Which machine is best for a network scan? Which should handle data analysis? NACC uses AI to make these decisions."

**Show**: Architecture diagram from README or draw on whiteboard:
```
Mac (Orchestrator) 
    ↓ (AI decides)
    ↓
Kali VM → Security/Network tasks
Windows VM → Windows-specific tasks
Physical laptop → Local development
```

---

## Demo Part 2: AI Routing in Action (3 minutes)

**Say**: "Let me show you the AI making a real decision. I'll ask it to run a network scan."

**Command 1 - AI Health Check**:
```bash
nacc-orchestrator agents-check --config configs/orchestrator-vms.yml \
  --message "Are all systems operational?"
```

**Point out**:
- AI responds with health status
- Uses natural language understanding
- This is Docker Desktop AI (Mistral-NeMo 12B params)

**Command 2 - Intelligent Routing**:
```bash
nacc-orchestrator exec --config configs/orchestrator-vms.yml \
  --description "Run network scan" \
  --cmd nmap --version
```

**Point out**:
- AI analyzes the request: "network scan"
- Looks at available nodes and their tags
- Chooses `kali-vm` because it has tags: `[kali, pentesting, network-tools]`
- Executes on the VM automatically
- Show the JSON output with `router_reason`

---

## Demo Part 3: MCP Tools in Action (3 minutes)

**Say**: "NACC is fully MCP-compliant. Let me demonstrate the protocol tools."

**Command 3 - List Files**:
```bash
nacc-orchestrator mcp ListFiles --config configs/orchestrator-vms.yml \
  --node-id kali-vm --path /home/vasanth
```

**Point out**: Remote file browsing through MCP

**Command 4 - Execute Command**:
```bash
nacc-orchestrator mcp ExecuteCommand --config configs/orchestrator-vms.yml \
  --node-id kali-vm --command "uname -a"
```

**Point out**: 
- Command executes on Kali VM
- Security whitelist enforced (try `rm -rf /` - will fail!)
- All operations logged for audit

**Command 5 - Get Node Info**:
```bash
nacc-orchestrator mcp GetNodeInfo --config configs/orchestrator-vms.yml \
  --node-id kali-vm
```

**Point out**:
- System metrics (CPU, memory, disk)
- Network info
- Capabilities/tags

---

## Demo Part 4: The Dashboard (2 minutes)

**Say**: "All of this has a web UI too."

**Launch**:
```bash
nacc-ui serve --config configs/ui-config.yml --share
```

**Show**:
1. Nodes tab - see Kali VM status
2. Files tab - browse remote filesystem
3. Execute tab - run commands with logs
4. Agents tab - test AI routing

---

## Demo Part 5: Technical Deep Dive (2 minutes)

**Open VS Code** and show:

1. **`src/nacc_orchestrator/agents.py`** - DockerMistralBackend class
   - Point out: Uses `docker model run` to interact with AI
   - Show prompt construction
   
2. **`configs/orchestrator-vms.yml`** - Configuration
   - Point out: Backend is `docker-mistral` with `mistral-nemo` model
   
3. **`configs/node-kali-vm.yml`** - Node security
   - Point out: `allowed_commands` whitelist
   - Explain: Prevents malicious execution

4. **`tests/`** - Testing
   - Run: `pytest tests/ -v`
   - Show: 21 tests passing

---

## Demo Part 6: Real-World Use Case (2 minutes)

**Say**: "Here's a practical scenario..."

**Scenario**: Security audit across infrastructure

**Command**:
```bash
nacc-orchestrator exec --config configs/orchestrator-vms.yml \
  --description "Check for open ports on all machines" \
  --cmd nmap --args "-p-" --args "192.168.64.0/24"
```

**Say**: 
- AI routes to Kali (security/network tools)
- Executes nmap scan
- Results logged centrally
- Scales to 10, 100, 1000 nodes

---

## Demo Part 7: Future Roadmap (1 minute)

**Say**: "This is just the beginning. Next steps:"

1. ✅ Add Windows VM support (code ready, just need VM)
2. ✅ Add Mac as local node (config commented out)
3. 🔄 Add cloud VMs (AWS/GCP) - same code, just SSH
4. 🔄 Streaming logs in UI
5. 🔄 Multi-agent collaboration (Router → Security → Execution)
6. 🔄 IDE integration (VS Code extension)

**Show**: Roadmap in README or HACKATHON-READY.md

---

## Closing (1 minute)

**Key Points**:
1. ✨ Real AI routing (not heuristics) - Docker Desktop AI
2. 🖥️ Real VM control (Kali Linux on UTM)
3. 🔧 Full MCP protocol compliance (6 tools)
4. 🔒 Production-ready (security, logging, tests)
5. 📈 Scales to any infrastructure (VMs, containers, physical machines)

**Differentiators**:
- Most MCP servers are single-machine
- NACC orchestrates entire networks
- AI-powered routing across heterogeneous systems
- Enterprise-grade security and auditability

**Repository**: [Show GitHub/local repo]

---

## Backup Commands (If Demo Fails)

If Kali VM is down:
```bash
# Use localhost mode
nacc-orchestrator exec --config configs/orchestrator-local.yml \
  --description "Check system info" --cmd uname --args "-a"
```

If Docker AI is slow:
```bash
# Use heuristic fallback
# Edit orchestrator-vms.yml: kind: heuristic
```

If network issues:
```bash
# Show pre-recorded video from scripts/full_demo.sh
```

---

## Q&A Preparation

**Q: Why Docker AI instead of API-based LLMs?**
A: Docker Desktop AI runs locally, no API costs, no privacy concerns, fast inference on Apple Silicon.

**Q: How do you secure remote execution?**
A: Three layers: 1) Command whitelist, 2) SSH key auth, 3) Audit logging. All configurable per node.

**Q: Can this work with Windows/Mac nodes?**
A: Yes! Node server is cross-platform Python. Windows VM config is ready, just needs deployment.

**Q: What about network failures?**
A: Orchestrator has timeouts, retries, and health checks. Nodes report status every 30s.

**Q: How does this compare to Ansible/Terraform?**
A: Ansible is configuration management (declarative). NACC is imperative command execution with AI routing. Complementary, not competitive.

**Q: Can I use this in production?**
A: Yes! Add TLS, use systemd for node daemon, configure firewall rules. See VM-SETUP-GUIDE.md.

---

## Timing

- Part 1 (Problem): 1 min
- Part 2 (AI Routing): 3 min
- Part 3 (MCP Tools): 3 min
- Part 4 (Dashboard): 2 min
- Part 5 (Code): 2 min
- Part 6 (Use Case): 2 min
- Part 7 (Roadmap): 1 min
- Closing: 1 min
**Total: ~15 minutes**

Buffer for questions: 5 minutes
**Grand Total: 20 minutes**
