#!/usr/bin/env bash
# Quick AI Routing Test - Demonstrates Docker AI making intelligent decisions
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"
source .venv/bin/activate

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}🤖 Testing AI-Powered Routing with Docker Mistral-NeMo${NC}"
echo "============================================================"
echo ""

# Test 1: Network scan task (should route to Kali)
echo -e "${YELLOW}Test 1: Network scanning task${NC}"
echo "Command: nmap --version"
echo "Expected: AI should choose kali-vm due to pentesting tags"
echo ""
nacc-orchestrator exec --config configs/orchestrator-vms.yml \
    --description "Run network scan tool" \
    --cmd nmap --version | jq -r '.plan.router_reason' | sed 's/^/  AI Decision: /'
echo ""

# Test 2: File listing (should work on any node)
echo -e "${YELLOW}Test 2: File listing task${NC}"
echo "Command: ls -la"
echo "Expected: AI should choose based on availability"
echo ""
nacc-orchestrator exec --config configs/orchestrator-vms.yml \
    --description "List files in directory" \
    --cmd ls -la | jq -r '.plan.router_reason' | sed 's/^/  AI Decision: /'
echo ""

# Test 3: System info (should work on any Linux node)
echo -e "${YELLOW}Test 3: System information task${NC}"
echo "Command: uname -a"
echo "Expected: AI should choose based on system capabilities"
echo ""
nacc-orchestrator exec --config configs/orchestrator-vms.yml \
    --description "Get system information" \
    --cmd uname -a | jq -r '.plan.router_reason' | sed 's/^/  AI Decision: /'
echo ""

echo -e "${GREEN}✨ AI Routing Tests Complete!${NC}"
echo ""
echo "Notice how the AI:"
echo "  1. Understands task context (network scanning, file ops, system info)"
echo "  2. Matches node capabilities (kali, pentesting tags)"
echo "  3. Provides reasoning for each decision"
echo ""
echo "This is NOT hardcoded routing - it's real LLM decision-making!"
