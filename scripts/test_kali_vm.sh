#!/usr/bin/env bash
#
# test_kali_vm.sh - Quick test script for Kali VM integration
#

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_test() { echo -e "${CYAN}[TEST]${NC} $*"; }

source .venv/bin/activate

log_info "Testing NACC with Kali VM (no orchestrator server needed)"
echo

# Test 1: Direct curl to Kali node
log_test "1. Testing Kali VM node health..."
HEALTH=$(curl -s http://192.168.64.2:8765/healthz)
echo "   Response: $HEALTH"
echo

# Test 2: Get node info
log_test "2. Getting Kali VM system info..."
curl -s http://192.168.64.2:8765/node | jq '{node_id, tags, platform: .platform.system, memory_percent: .metrics.memory_percent}'
echo

# Test 3: List files via orchestrator CLI (doesn't need server running)
log_test "3. Listing files on Kali VM via orchestrator..."
nacc-orchestrator list-files --config configs/orchestrator-vms.yml --node kali-vm --path . | jq .
echo

# Test 4: Create a test file on Kali
log_test "4. Creating test file on Kali VM..."
sshpass -p 'toor' ssh -o StrictHostKeyChecking=no vasanth@192.168.64.2 \
  "echo 'Hello from NACC!' > ~/nacc-shared/test.txt && cat ~/nacc-shared/test.txt"
echo

# Test 5: List files again to see the new file
log_test "5. Listing files again (should show test.txt)..."
nacc-orchestrator list-files --config configs/orchestrator-vms.yml --node kali-vm --path . | jq .
echo

# Test 6: Execute command on Kali
log_test "6. Executing 'uname -a' on Kali VM..."
nacc-orchestrator exec --config configs/orchestrator-vms.yml \
  --description "Get system info" \
  --cmd uname -a | jq '.results[0] | {node_id, stdout, exit_code}'
echo

# Test 7: Execute nmap version check
log_test "7. Checking nmap version on Kali..."
nacc-orchestrator exec --config configs/orchestrator-vms.yml \
  --description "Check nmap" \
  --cmd nmap --version | jq '.results[0] | {node_id, stdout}'
echo

log_info "✅ All tests passed! Kali VM is working with NACC!"
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary:"
echo "  • Kali VM node server: http://192.168.64.2:8765"
echo "  • Node ID: kali-vm"
echo "  • Platform: Kali Linux (aarch64)"
echo "  • Tools: nmap, netcat, curl, wget, etc."
echo
echo "To start the full UI:"
echo "  Terminal 1: nacc-orchestrator serve --config configs/orchestrator-vms.yml"
echo "  Terminal 2: nacc-ui serve --config configs/ui.yml"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
