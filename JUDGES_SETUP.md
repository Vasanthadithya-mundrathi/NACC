# ⚖️ NACC Setup Guide for Judges

**Goal**: Get NACC running on your machine in under 2 minutes.

## ⚡ Quick Start (Copy & Paste)

Open your terminal and run these commands block-by-block.

### 1. Install & Setup
```bash
# Clone the repo
git clone https://github.com/Vasanthadithya-mundrathi/NACC.git
cd NACC

# Setup Environment (Mac/Linux)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Make scripts executable
chmod +x start_nacc.sh
```

### 2. Run the System
```bash
# This starts the Orchestrator and the UI
./start_nacc.sh
```

### 3. Use the UI
1.  Click the local URL shown in the terminal (usually `http://127.0.0.1:7860`).
2.  **That's it!** You are now chatting with the NACC Orchestrator.

---

## 🧪 Verification Steps

To verify everything is working perfectly:

1.  **Check the "About" Tab**:
    *   Go to the "About Creator & NACC" section.
    *   Verify that the Architecture Diagrams are visible.

2.  **Test the Chat**:
    *   Type: `Hello, who are you?`
    *   The AI should respond identifying itself as the NACC Orchestrator.

3.  **Test a Tool (Local Execution)**:
    *   Type: `List the files in the current directory`
    *   The AI should use the `list_directory` tool and show you the project files.

## ❓ FAQ for Judges

**Q: Do I need an API Key?**
A: NACC comes configured to use **Blaxel (Serverless)** by default, which may require a key if the trial is exhausted. However, you can also select **"Local (Docker)"** from the settings if you have them running, or simply provide your own OpenAI/Anthropic/gemini key in the UI settings.

**Q: I'm on Windows.**
A: Please use **WSL2** for the best experience. If running natively, use:
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m nacc_ui.cli
```

**Q: It says "Port already in use".**
A: The system automatically finds the next open port. Check the terminal for the correct URL (e.g., `http://127.0.0.1:7861`).
