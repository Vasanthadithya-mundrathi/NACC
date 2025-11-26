# 🚀 NACC Setup Guide: Zero to Hero

Welcome to the **Network Agentic Connection Call (NACC)** setup guide. This document will take you from a fresh machine to a fully orchestrated multi-node AI system.

## 📋 Prerequisites

Before you begin, ensure you have the following:

- **Operating System**: macOS, Linux, or Windows (WSL2 recommended).
- **Python**: Version 3.10 or higher.
- **Git**: For cloning the repository.
- **Node.js & npm** (Optional): Only if you plan to modify the frontend extensively.

## 🛠️ Step 1: Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/Vasanthadithya-mundrathi/NACC.git
    cd NACC
    ```

2.  **Create a Virtual Environment**
    It's best practice to isolate dependencies.
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

## ⚙️ Step 2: Configuration

NACC uses a flexible configuration system. You can use local LLMs (Ollama), Docker containers, or cloud APIs (OpenAI, Anthropic, Blaxel).

1.  **Set up API Keys (Optional)**
    If you want to use cloud models, create a `.env` file or export variables:
    ```bash
    export OPENAI_API_KEY="sk-..."
    export ANTHROPIC_API_KEY="sk-ant-..."
    export BLAXEL_API_KEY="..."
    ```

2.  **Review Config Files**
    Check `configs/ui-config.example.yml` to see how the UI is configured. You can create a copy `configs/ui-config.yml` to customize it.

## 🚀 Step 3: Running the Orchestrator

The Orchestrator is the "brain" of the system. It hosts the API and the Web UI.

1.  **Start the System**
    We provide a handy script to start everything at once:
    ```bash
    ./start_nacc.sh
    ```
    *This script checks for dependencies, sets up the environment, and launches the UI.*

2.  **Access the UI**
    Open your browser and navigate to:
    `http://127.0.0.1:7860`

## 💻 Step 4: Connecting Nodes (Agents)

To make NACC truly powerful, you connect "Nodes" - other computers or VMs that the AI can control.

1.  **On the Target Machine (Node)**
    *   Install NACC (Steps 1-3 above).
    *   Initialize the Node:
        ```bash
        nacc-node init --name "My-MacBook" --host 0.0.0.0 --port 8001
        ```

2.  **On the Orchestrator Machine**
    *   Register the new Node:
        ```bash
        nacc-orchestrator register-node --name "My-MacBook" --url "http://<NODE_IP>:8001"
        ```

3.  **Verify Connection**
    In the NACC UI chat, type:
    > "List all connected nodes"
    
    The AI should confirm that "My-MacBook" is available.

## 🛡️ Windows Compatibility Note

NACC is designed primarily for Unix-like environments (macOS, Linux).
*   **Windows Users**: We strongly recommend using **WSL2 (Windows Subsystem for Linux)**.
*   **Native Windows**: While Python code is cross-platform, some specific "Shell" tools used by the agents might expect Bash syntax (e.g., `ls`, `grep`). If running natively on Windows, the agent may need to be instructed to use PowerShell commands.

## 🆘 Troubleshooting

*   **Port Conflicts**: If port 7860 is busy, the UI will try the next available port. Check the terminal output.
*   **Missing Dependencies**: Run `pip install -r requirements.txt` again.
*   **Permission Denied**: Ensure `start_nacc.sh` is executable (`chmod +x start_nacc.sh`).
