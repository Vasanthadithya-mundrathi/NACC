# 💡 NACC Usage Examples

Here are three scenarios to demonstrate the power of the Network Agentic Connection Call (NACC) system.

## 📂 Scenario 1: Basic File Operations (Local Node)

**Goal**: Ask the AI to organize your files.

**Prompt**:
> "Create a directory called 'test_data', write a file named 'notes.txt' inside it with the text 'Hello World', and then read it back to me."

**What Happens**:
1.  **Intent Parser**: Identifies 3 steps (Create Dir, Write File, Read File).
2.  **Orchestrator**: Executes them sequentially on the local node.
3.  **Result**: You see the file content "Hello World" in the chat.

## 🛡️ Scenario 2: Network Security Scan (Kali Node)

*Requires a connected Kali Linux node.*

**Goal**: Scan a target IP for vulnerabilities.

**Prompt**:
> "Switch to the Kali node. Run an nmap scan on 192.168.1.50 to find open ports. If you find port 80, try to curl the homepage."

**What Happens**:
1.  **Router**: Routes the request to the `kali-node`.
2.  **Agent**: Executes `nmap -F 192.168.1.50`.
3.  **Logic**: If output contains "80/tcp open", the Agent executes `curl http://192.168.1.50`.
4.  **Result**: The AI summarizes the open ports and the web page content.

## 🔄 Scenario 3: Multi-Node Workflow

*Requires multiple connected nodes.*

**Goal**: Distributed task execution.

**Prompt**:
> "Check the CPU usage on the MacBook node, and if it's below 50%, tell the Cloud node to start the backup process."

**What Happens**:
1.  **Orchestrator**: Queries MacBook node for `top -l 1 | grep CPU`.
2.  **Orchestrator**: Analyzes the result.
3.  **Orchestrator**: If condition met, sends command `python backup_script.py` to Cloud node.
4.  **Result**: A coordinated action across two different physical machines.
