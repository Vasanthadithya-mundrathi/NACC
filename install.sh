#!/bin/bash

# NACC Setup Script
# Installs dependencies and prepares the environment for the MCP Birthday Hackathon

set -e

echo "🚀 Setting up NACC (Network Agentic Connection Call)..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed."
    exit 1
fi

echo "✅ Python 3 detected."

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
else
    echo "📦 Virtual environment already exists."
fi

# Activate venv
source .venv/bin/activate

# Install dependencies
echo "⬇️ Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# Create config directories if they don't exist
mkdir -p configs logs

# Check for config files
if [ ! -f "configs/orchestrator.yml" ]; then
    if [ -f "configs/orchestrator-blaxel-openai.yml" ]; then
        echo "📄 Copying Blaxel config to default orchestrator.yml..."
        cp configs/orchestrator-blaxel-openai.yml configs/orchestrator.yml
    else
        echo "⚠️ No default config found. Please configure configs/orchestrator.yml"
    fi
fi

if [ ! -f "configs/ui-config.yml" ]; then
    if [ -f "configs/ui-config.example.yml" ]; then
        cp configs/ui-config.example.yml configs/ui-config.yml
    fi
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the system, run:"
echo "  ./start_nacc.sh"
echo ""
echo "Or run components individually:"
echo "  nacc-orchestrator serve"
echo "  nacc-ui"
echo ""
