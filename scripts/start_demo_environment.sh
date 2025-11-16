#!/usr/bin/env bash
# Start Demo Environment - Launches all NACC components in order
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Starting NACC Demo Environment"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Kali VM is accessible
echo -e "${YELLOW}1. Checking Kali VM connectivity...${NC}"
if ping -c 1 192.168.64.2 &> /dev/null; then
    echo -e "${GREEN}✓ Kali VM is reachable${NC}"
else
    echo "❌ Kali VM (192.168.64.2) is not reachable. Please start UTM VM."
    exit 1
fi

# Restart Kali node server
echo ""
echo -e "${YELLOW}2. Restarting Kali node server...${NC}"

# Kill existing processes
sshpass -p 'toor' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 vasanth@192.168.64.2 "pkill -f 'nacc-node' || true" 2>/dev/null || true

sleep 2

# Start node server using Python module
sshpass -p 'toor' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 vasanth@192.168.64.2 \
    'cd ~/nacc && source .venv/bin/activate && export PYTHONPATH=$HOME/nacc/src:$PYTHONPATH && nohup python3 -m nacc_node.cli serve --config node-config.yml --host 0.0.0.0 --port 8765 > node.log 2>&1 &' 2>/dev/null

sleep 3

# Verify node is responding
if curl -s http://192.168.64.2:8765/healthz 2>/dev/null | grep -q "ok"; then
    echo -e "${GREEN}✓ Kali node server is running${NC}"
else
    echo "❌ Kali node server failed to start"
    echo "Checking node log..."
    sshpass -p 'toor' ssh vasanth@192.168.64.2 "tail -20 ~/nacc/node.log"
    exit 1
fi

# Start orchestrator in background
echo ""
echo -e "${YELLOW}3. Starting orchestrator...${NC}"
cd "$PROJECT_ROOT"

# Activate venv
if [ ! -f ".venv/bin/activate" ]; then
    echo "❌ Virtual environment not found. Run ./setup_nacc.sh first."
    exit 1
fi

source .venv/bin/activate

# Kill any existing orchestrator
pkill -f 'nacc-orchestrator' || true
sleep 1

# Start orchestrator
nohup nacc-orchestrator serve --config configs/orchestrator-vms.yml --host 127.0.0.1 --port 8888 > .orchestrator.log 2>&1 &
ORCHESTRATOR_PID=$!
echo "Started orchestrator with PID: $ORCHESTRATOR_PID"

# Wait for startup
sleep 5

# Check if still running
if ! ps -p $ORCHESTRATOR_PID > /dev/null 2>&1; then
    echo "❌ Orchestrator failed to start. Check .orchestrator.log:"
    tail -20 .orchestrator.log
    exit 1
fi

# Test orchestrator API
for i in {1..10}; do
    if curl -s http://127.0.0.1:8888/nodes &> /dev/null; then
        echo -e "${GREEN}✓ Orchestrator is running and responding${NC}"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "❌ Orchestrator API is not responding after 10 attempts"
        tail -20 .orchestrator.log
        exit 1
    fi
    sleep 1
done

echo ""
echo -e "${GREEN}=================================="
echo "✨ Demo Environment Ready!"
echo "==================================${NC}"
echo ""
echo "Services running:"
echo "  - Kali Node: http://192.168.64.2:8765"
echo "  - Orchestrator: http://127.0.0.1:8888"
echo ""
echo "Next steps:"
echo "  1. Test AI routing: ./scripts/test_ai_routing.sh"
echo "  2. Run full demo: ./scripts/full_demo.sh"
echo "  3. Start UI: nacc-ui serve --config configs/ui-config.yml --share"
echo ""
echo "Logs:"
echo "  - Orchestrator: tail -f .orchestrator.log"
echo "  - Kali Node: sshpass -p 'toor' ssh vasanth@192.168.64.2 'tail -f ~/nacc/node.log'"
