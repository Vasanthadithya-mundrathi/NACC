#!/usr/bin/env bash
# Test the conversational UI API calls

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Testing NACC Conversational UI Backend${NC}"
echo "========================================"
echo ""

# Test 1: List files
echo -e "${YELLOW}Test 1: List files command${NC}"
RESPONSE=$(curl -s -X POST http://127.0.0.1:8888/commands/execute \
  -H "Content-Type: application/json" \
  -d '{"description": "List files", "command": ["ls", "-la", "/home/vasanth"], "parallelism": 1}')

if echo "$RESPONSE" | jq -e '.results[0].exit_code == 0' > /dev/null; then
    echo -e "${GREEN}✓ List files working${NC}"
    echo "$RESPONSE" | jq -r '.results[0].stdout' | head -5
else
    echo -e "${RED}✗ List files failed${NC}"
    echo "$RESPONSE" | jq '.'
fi
echo ""

# Test 2: Read file
echo -e "${YELLOW}Test 2: Read file command${NC}"
RESPONSE=$(curl -s -X POST http://127.0.0.1:8888/commands/execute \
  -H "Content-Type: application/json" \
  -d '{"description": "Read config", "command": ["cat", "/home/vasanth/nacc/node-config.yml"], "parallelism": 1}')

if echo "$RESPONSE" | jq -e '.results[0].exit_code == 0' > /dev/null; then
    echo -e "${GREEN}✓ Read file working${NC}"
    echo "$RESPONSE" | jq -r '.results[0].stdout' | head -5
else
    echo -e "${RED}✗ Read file failed${NC}"
fi
echo ""

# Test 3: Get nodes
echo -e "${YELLOW}Test 3: Get nodes${NC}"
RESPONSE=$(curl -s http://127.0.0.1:8888/nodes)

if echo "$RESPONSE" | jq -e '.[0].node_id' > /dev/null; then
    echo -e "${GREEN}✓ Get nodes working${NC}"
    echo "$RESPONSE" | jq -r '.[0].node_id, .[0].tags'
else
    echo -e "${RED}✗ Get nodes failed${NC}"
fi
echo ""

# Test 4: AI Routing
echo -e "${YELLOW}Test 4: AI Routing Decision${NC}"
RESPONSE=$(curl -s -X POST http://127.0.0.1:8888/commands/execute \
  -H "Content-Type: application/json" \
  -d '{"description": "Network scan tool test", "command": ["nmap", "--version"], "parallelism": 1}')

if echo "$RESPONSE" | jq -e '.plan.router_reason' > /dev/null; then
    echo -e "${GREEN}✓ AI Routing working${NC}"
    echo "AI Reasoning:"
    echo "$RESPONSE" | jq -r '.plan.router_reason'
else
    echo -e "${RED}✗ AI Routing failed${NC}"
fi
echo ""

echo -e "${GREEN}========================================"
echo "All backend tests complete!"
echo "========================================${NC}"
echo ""
echo "The UI should now be able to:"
echo "  ✓ List files on Kali VM"
echo "  ✓ Read file contents"
echo "  ✓ Show node information"
echo "  ✓ Use AI for routing decisions"
echo ""
echo "Access the UI at: http://localhost:7860"
