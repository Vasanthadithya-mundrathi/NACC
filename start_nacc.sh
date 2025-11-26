#!/bin/bash
# NACC Startup Script - Blaxel Backend (Default for Judges)
# This script starts all NACC components with Blaxel backend

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "🚀 Starting NACC with Blaxel Backend"
echo "====================================="
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python3 -m venv .venv && source .venv/bin/activate && pip install -e ."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# MODAL CHECKS COMMENTED OUT - Using Blaxel instead
# if ! command -v modal &> /dev/null; then
#     echo "❌ Modal CLI not found!"
#     echo "Installing Modal..."
#     pip install modal
# fi

echo "✅ Virtual environment activated"
echo ""

# MODAL AUTHENTICATION COMMENTED OUT
# if ! modal token current &> /dev/null; then
#     echo "⚠️  Modal not authenticated"
#     echo "Please run: modal token new"
#     echo ""
#     read -p "Press Enter to authenticate now, or Ctrl+C to exit..."
#     modal token new
# fi

# echo "✅ Modal authenticated"
# echo ""

# Create logs directory
mkdir -p logs

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Stopping NACC components..."
    # kill $MODAL_PID 2>/dev/null || true  # Modal not used
    kill $ORCHESTRATOR_PID 2>/dev/null || true
    kill $UI_PID 2>/dev/null || true
    echo "✅ Cleanup complete"
    exit 0
}

trap cleanup SIGINT SIGTERM

# MODAL SERVE COMMENTED OUT - Using Blaxel backend instead
# echo "1️⃣  Starting Modal backend..."
# modal serve src/nacc_orchestrator/modal_backend.py > logs/modal.log 2>&1 &
# MODAL_PID=$!
# echo "   Modal PID: $MODAL_PID"
# echo "   Waiting for Modal to be ready..."
# sleep 5

# if ! kill -0 $MODAL_PID 2>/dev/null; then
#     echo "❌ Modal failed to start. Check logs/modal.log"
#     exit 1
# fi
# echo "✅ Modal backend ready"
# echo ""

# Start Orchestrator in background (using Blaxel config)
echo "1️⃣  Starting NACC Orchestrator (with Blaxel backend)..."
nacc-orchestrator serve --config configs/orchestrator-blaxel-openai.yml > logs/orchestrator.log 2>&1 &
ORCHESTRATOR_PID=$!
echo "   Orchestrator PID: $ORCHESTRATOR_PID"
echo "   Waiting for orchestrator to be ready..."
sleep 3

# Check if orchestrator is running
if ! kill -0 $ORCHESTRATOR_PID 2>/dev/null; then
    echo "❌ Orchestrator failed to start. Check logs/orchestrator.log"
    exit 1
fi
echo "✅ Orchestrator ready at http://localhost:8888"
echo ""

# Start UI in background (using example config, not modal-specific)
echo "2️⃣  Starting NACC UI..."
nacc-ui --config configs/ui-config.example.yml --share > logs/ui.log 2>&1 &
UI_PID=$!
echo "   UI PID: $UI_PID"
echo "   Waiting for UI to be ready..."
sleep 3

# Check if UI is running
if ! kill -0 $UI_PID 2>/dev/null; then
    echo "❌ UI failed to start. Check logs/ui.log"
    kill $ORCHESTRATOR_PID 2>/dev/null || true
    exit 1
fi

# Extract public URL from UI logs
sleep 2
PUBLIC_URL=$(grep -o 'https://[^[:space:]]*gradio.live' logs/ui.log | head -1)

echo "✅ UI ready"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 NACC is running with Blaxel backend!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Dashboard URLs:"
echo "   Local:  http://localhost:7860"
if [ -n "$PUBLIC_URL" ]; then
    echo "   Public: $PUBLIC_URL"
fi
echo ""
echo "🔧 API Endpoint:"
echo "   http://localhost:8888"
echo ""
echo "📝 Logs:"
echo "   Orchestrator: logs/orchestrator.log"
echo "   UI:           logs/ui.log"
echo ""
echo "💡 Try these commands in the UI:"
echo "   - switch to kali-vm"
echo "   - list files"
echo "   - write hello world to test.txt"
echo "   - read file test.txt"
echo ""
echo "Press Ctrl+C to stop all services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Keep script running and show log tails
while true; do
    sleep 5
    # Check if any process died (Modal check removed)
    if ! kill -0 $ORCHESTRATOR_PID 2>/dev/null; then
        echo "❌ Orchestrator process died!"
        cleanup
    fi
    if ! kill -0 $UI_PID 2>/dev/null; then
        echo "❌ UI process died!"
        cleanup
    fi
done
