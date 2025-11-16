#!/usr/bin/env bash
#
# deploy_to_kali.sh - Quick deployment script for Kali VM only
#

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Kali VM details
KALI_HOST="192.168.64.2"
KALI_USER="vasanth"
KALI_PASS="toor"

log_info "Testing Kali VM connectivity..."
if ! ping -c 1 -W 2 "$KALI_HOST" &> /dev/null; then
    log_error "Cannot reach Kali VM at $KALI_HOST"
    exit 1
fi

if ! sshpass -p "$KALI_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
    "$KALI_USER@$KALI_HOST" "echo 'SSH OK'" &> /dev/null; then
    log_error "SSH to Kali VM failed"
    exit 1
fi

log_info "✅ Kali VM is reachable"

# Create deployment package
log_info "Creating deployment package..."
TEMP_DIR=$(mktemp -d)
trap "rm -rf '$TEMP_DIR'" EXIT

mkdir -p "$TEMP_DIR/nacc/src"
cp -r src/nacc_node "$TEMP_DIR/nacc/src/"
cp pyproject.toml "$TEMP_DIR/nacc/"
cp configs/node-kali-vm.yml "$TEMP_DIR/nacc/node-config.yml"

# Create installation script for the VM
cat > "$TEMP_DIR/nacc/install.sh" << 'INSTALL_SCRIPT'
#!/bin/bash
set -e
echo "[INFO] Installing NACC node on Kali VM..."

# Create directories
mkdir -p ~/nacc-shared ~/nacc-backup ~/nacc-sync

# Setup virtual environment
cd ~/nacc
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install pydantic pyyaml psutil requests

# Make nacc_node importable
export PYTHONPATH="$HOME/nacc/src:$PYTHONPATH"

echo "[INFO] Installation complete!"
echo "[INFO] To start the node server:"
echo "  cd ~/nacc"
echo "  source .venv/bin/activate"
echo "  export PYTHONPATH=\$HOME/nacc/src:\$PYTHONPATH"
echo "  python3 -m nacc_node.cli serve --config node-config.yml --host 0.0.0.0 --port 8765"
INSTALL_SCRIPT

chmod +x "$TEMP_DIR/nacc/install.sh"

# Package it
cd "$TEMP_DIR"
tar czf nacc-package.tar.gz nacc/

# Deploy to Kali
log_info "Deploying to Kali VM..."

sshpass -p "$KALI_PASS" ssh -o StrictHostKeyChecking=no "$KALI_USER@$KALI_HOST" "
    rm -rf ~/nacc
    mkdir -p ~/nacc
"

sshpass -p "$KALI_PASS" scp -o StrictHostKeyChecking=no \
    "$TEMP_DIR/nacc-package.tar.gz" \
    "$KALI_USER@$KALI_HOST:~/nacc-package.tar.gz"

log_info "Installing on Kali VM..."
sshpass -p "$KALI_PASS" ssh -o StrictHostKeyChecking=no "$KALI_USER@$KALI_HOST" "
    cd ~
    tar xzf nacc-package.tar.gz
    cd nacc
    bash install.sh
"

log_info "✅ Deployment complete!"
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Next steps:"
echo
echo "1️⃣  Start the node server on Kali VM:"
echo "   ssh vasanth@192.168.64.2"
echo "   cd ~/nacc && source .venv/bin/activate"
echo "   export PYTHONPATH=\$HOME/nacc/src:\$PYTHONPATH"
echo "   python3 -m nacc_node.cli serve --config node-config.yml --host 0.0.0.0 --port 8765"
echo
echo "2️⃣  Test from your Mac:"
echo "   curl http://192.168.64.2:8765/healthz"
echo
echo "3️⃣  Start the orchestrator (in a new terminal on your Mac):"
echo "   cd '$PROJECT_ROOT'"
echo "   source .venv/bin/activate"
echo "   nacc-orchestrator serve --config configs/orchestrator-vms.yml"
echo
echo "4️⃣  Test the full stack:"
echo "   nacc-orchestrator list-files --config configs/orchestrator-vms.yml --node kali-vm --path ."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
