#!/usr/bin/env bash
#
# full_demo.sh - Complete NACC demonstration with Docker AI
#

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
MAGENTA='\033[0;35m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_demo() { echo -e "${MAGENTA}[DEMO]${NC} $*"; }
log_ai() { echo -e "${CYAN}[AI]${NC} $*"; }

source .venv/bin/activate

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   NACC - Network Agentic Connection Call"
echo "   AI-Powered Multi-Machine Orchestration Platform"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

log_info "Using Docker AI Model: Mistral-NeMo"
docker model list | grep mistral-nemo
echo

log_demo "═══ Demo 1: AI Health Check ═══"
log_ai "Testing Docker AI integration..."
nacc-orchestrator agents-check --config configs/orchestrator-vms.yml --message "NACC system ready" | jq '{message, response: (.response | fromjson? // .response)}'
echo

log_demo "═══ Demo 2: Node Discovery ═══"
log_info "Connected nodes:"
curl -s http://192.168.64.2:8765/node | jq '{node_id, platform: .platform.system, tags, memory_percent: .metrics.memory_percent}'
echo

log_demo "═══ Demo 3: AI-Powered Routing ═══"
log_ai "AI will decide which node to use for a security scan..."
nacc-orchestrator exec --config configs/orchestrator-vms.yml \
  --description "Run nmap scan" \
  --cmd nmap --version | jq '{
    selected_node: .plan.nodes[0],
    ai_reasoning: .plan.router_reason,
    execution: {
      stdout: .results[0].stdout | split("\n")[0],
      exit_code: .results[0].exit_code,
      duration: .results[0].duration
    }
  }'
echo

log_demo "═══ Demo 4: File Operations ═══"
log_info "Creating test file on Kali VM..."
sshpass -p 'toor' ssh -o StrictHostKeyChecking=no vasanth@192.168.64.2 \
  "date > ~/nacc-shared/demo-$(date +%s).txt"

log_info "Listing files via MCP protocol..."
nacc-orchestrator list-files --config configs/orchestrator-vms.yml \
  --node kali-vm --path . | jq '{node_id, file_count: .count, files: [.files[].relative_path]}'
echo

log_demo "═══ Demo 5: Remote Command Execution ═══"
log_info "Running system commands on Kali VM..."
nacc-orchestrator exec --config configs/orchestrator-vms.yml \
  --description "Get hostname" \
  --cmd hostname | jq '.results[0] | {node_id, stdout, exit_code}'
echo

nacc-orchestrator exec --config configs/orchestrator-vms.yml \
  --description "Check Python version" \
  --cmd python3 --version | jq '.results[0] | {node_id, stdout}'
echo

log_demo "═══ Demo 6: Multi-Tool Test ═══"
log_info "Testing various security tools..."
for tool in nmap curl wget ping; do
  echo "  → Testing $tool..."
  nacc-orchestrator exec --config configs/orchestrator-vms.yml \
    --description "Test $tool" \
    --cmd $tool --version 2>/dev/null | jq -r '.results[0].stdout' | head -1
done
echo

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_info "✅ ALL DEMOS COMPLETED SUCCESSFULLY!"
echo
echo "Key Features Demonstrated:"
echo "  ✓ Docker AI (Mistral-NeMo) for intelligent routing"
echo "  ✓ Real VM control (Kali Linux in UTM)"
echo "  ✓ MCP protocol compliance (ListFiles, ExecuteCommand)"
echo "  ✓ Agentic decision-making (AI chooses best node)"
echo "  ✓ Security tool orchestration (nmap, netcat, etc.)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
