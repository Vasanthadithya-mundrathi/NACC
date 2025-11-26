# NACC VM Setup Guide

## 🎯 Goal
Connect your MacBook (orchestrator) to real UTM VMs (Kali + Parrot OS) using Docker AI for agentic decision-making.

## 📋 Prerequisites

### On Your MacBook (Host/Orchestrator)
- ✅ Docker Desktop with Mistral-NeMo model (ccdfa597c64)
- ✅ Python 3.12 virtual environment (`.venv`)
- ✅ NACC project installed (`./setup_nacc.sh`)

### VM Network Details
- **Kali Linux**: 192.168.64.2 (username: `vasanth`, password: `toor`)
- **Parrot OS**: 192.168.64.3 (username: `user`, password: `parrot`)

---

## 🚀 Step-by-Step Setup

### Step 1: Start Your VMs in UTM

1. Open UTM on your Mac
2. Start **Kali Linux** VM
3. Start **Parrot OS** VM
4. Wait for both to boot completely

### Step 2: Enable SSH on VMs

#### On Kali Linux (from VM console):
```bash
# Start SSH service
sudo systemctl start ssh
sudo systemctl enable ssh

# Check SSH is running
sudo systemctl status ssh

# Verify IP address
ip addr show eth0 | grep "inet "
```

#### On Parrot OS (from VM console):
```bash
# Start SSH service
sudo systemctl start ssh
sudo systemctl enable ssh

# Check SSH is running
sudo systemctl status ssh

# Verify IP address
ip addr show enp0s1 | grep "inet "
```

### Step 3: Test Connectivity from Mac

```bash
# Test Kali
ssh vasanth@192.168.64.2
# Enter password: toor

# Test Parrot
ssh user@192.168.64.3
# Enter password: parrot
```

### Step 4: Install Python & Dependencies on VMs

#### On Kali Linux:
```bash
ssh vasanth@192.168.64.2

# Install Python if needed
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# Create project directory
mkdir -p ~/nacc
cd ~/nacc

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate
```

#### On Parrot OS:
```bash
ssh user@192.168.64.3

# Install Python if needed
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# Create project directory
mkdir -p ~/nacc
cd ~/nacc

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate
```

### Step 5: Transfer NACC Node Server to VMs

From your Mac:

```bash
cd "/Users/vasanthadithya/Documents/Projects/MCP birthday hackathon"

# Package the node server
tar czf nacc-node-package.tar.gz \
  src/nacc_node/ \
  pyproject.toml \
  setup_nacc.sh

# Copy to Kali
sshpass -p 'toor' scp nacc-node-package.tar.gz vasanth@192.168.64.2:~/nacc/

# Copy to Parrot
sshpass -p 'parrot' scp nacc-node-package.tar.gz user@192.168.64.3:~/nacc/
```

### Step 6: Install NACC on VMs

#### On Kali:
```bash
ssh vasanth@192.168.64.2
cd ~/nacc
tar xzf nacc-node-package.tar.gz
source .venv/bin/activate
pip install -e .
```

#### On Parrot:
```bash
ssh user@192.168.64.3
cd ~/nacc
tar xzf nacc-node-package.tar.gz
source .venv/bin/activate
pip install -e .
```

### Step 7: Configure Node Servers on VMs

#### On Kali (create `node-kali.yml`):
```yaml
node_id: kali-vm
root_dir: /home/vasanth/nacc-shared
description: Kali Linux pentesting node
tags: [kali, linux, pentesting, security]
allowed_commands: [python3, ls, cat, echo, nmap, netcat, ping, grep, find]
sync_targets:
  backup: /home/vasanth/nacc-backup
```

#### On Parrot (create `node-parrot.yml`):
```yaml
node_id: parrot-vm
root_dir: /home/user/nacc-shared
description: Parrot OS security node
tags: [parrot, linux, security, forensics]
allowed_commands: [python3, ls, cat, echo, nmap, ping, grep, find, wireshark]
sync_targets:
  backup: /home/user/nacc-backup
```

### Step 8: Start Node Servers on VMs

#### On Kali:
```bash
ssh vasanth@192.168.64.2
cd ~/nacc
mkdir -p nacc-shared nacc-backup
source .venv/bin/activate
nacc-node serve --config node-kali.yml --host 0.0.0.0 --port 8765
```

#### On Parrot:
```bash
ssh user@192.168.64.3
cd ~/nacc
mkdir -p nacc-shared nacc-backup
source .venv/bin/activate
nacc-node serve --config node-parrot.yml --host 0.0.0.0 --port 8766
```

---

## 🤖 Docker AI Model Setup

### Enable Docker Model API

```bash
# On your Mac
docker model list
# Should show: mistral-nemo (ccdfa597c644)

# Enable model runner on TCP port
docker desktop enable model-runner --tcp=12434

# Test the API
curl http://localhost:12434/engines/llama.cpp/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ccdfa597c644",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Say hello"}
    ]
  }'
```

---

## 🎮 Running the Complete NACC Stack

### 1. Start VMs and Node Servers (see Step 8)

### 2. Start Orchestrator on Mac

```bash
cd "/Users/vasanthadithya/Documents/Projects/MCP birthday hackathon"
source .venv/bin/activate

# Use the VM orchestrator config
nacc-orchestrator serve --config configs/orchestrator-vms.yml --host 127.0.0.1 --port 8888
```

### 3. Start UI on Mac

```bash
# In another terminal
cd "/Users/vasanthadithya/Documents/Projects/MCP birthday hackathon"
source .venv/bin/activate

nacc-ui serve --config configs/ui.yml --share
```

### 4. Test the Stack

```bash
# Check agent backend
nacc-orchestrator agents-check --config configs/orchestrator-vms.yml --message "test"

# List files on Kali
nacc-orchestrator list-files --config configs/orchestrator-vms.yml --node kali-vm --path .

# List files on Parrot
nacc-orchestrator list-files --config configs/orchestrator-vms.yml --node parrot-vm --path .

# Execute command (AI decides which VM)
nacc-orchestrator exec --config configs/orchestrator-vms.yml --description "Run nmap scan" --cmd nmap --version
```

---

## 🐛 Troubleshooting

### VMs not reachable
```bash
# Check VM IPs
ping 192.168.64.2
ping 192.168.64.3

# Check SSH
ssh vasanth@192.168.64.2
ssh user@192.168.64.3
```

### Node server not starting
```bash
# Check if port is in use
ssh vasanth@192.168.64.2 "netstat -tuln | grep 8765"

# Check firewall
ssh vasanth@192.168.64.2 "sudo ufw status"
```

### Docker AI not responding
```bash
# Check Docker Desktop is running
docker ps

# Check model list
docker model list

# Restart Docker Desktop if needed
```

---

## 📊 Demo Scenarios

### Scenario 1: File Operations
1. Create file on Mac
2. Sync to Kali VM
3. AI router decides to also backup to Parrot VM
4. Verify on both VMs

### Scenario 2: Security Scan
1. Ask AI: "Run a network scan"
2. Router agent chooses Kali (has `nmap` tag)
3. Execute `nmap` on Kali
4. Results returned to orchestrator

### Scenario 3: Multi-VM Task
1. Ask AI: "List all Python files on both VMs"
2. Router agent runs parallel queries
3. Aggregates results from Kali + Parrot
4. Display in UI

---

## 🎯 Next Steps

1. ✅ Start your VMs in UTM
2. ✅ Enable SSH on both VMs
3. ✅ Test connectivity from Mac
4. ✅ Install NACC node servers on VMs
5. ✅ Configure orchestrator to use Docker AI
6. ✅ Run the demo!
