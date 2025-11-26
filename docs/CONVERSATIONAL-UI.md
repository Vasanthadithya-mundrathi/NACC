# 💬 NACC Conversational UI

A ChatGPT-style interface for NACC with natural language control over your distributed infrastructure.

## 🎨 Interface Design

```
┌─────────────────────────────────────────────────────────────────┐
│  💬 Chat with NACC AI                │  📊 Preview & Output      │
│                                       │                           │
│  User: Hey, show me files on kali    │  📂 /home/vasanth        │
│                                       │  ├── Desktop/            │
│  AI: Sure! 📂 Using ListFiles tool   │  ├── Documents/          │
│      Here are the files:              │  ├── Downloads/          │
│      • Desktop/                       │  ├── nacc/               │
│      • Documents/                     │  └── nacc-shared/        │
│      • Downloads/                     │                           │
│      • nacc/                          │                           │
│                                       │                           │
│  User: Navigate to nacc folder        │  📄 node-config.yml     │
│                                       │                           │
│  AI: In a moment... 🔍                │  root_dir: /home/...    │
│      Folder contains:                 │  tags:                   │
│      • node-config.yml                │    - kali                │
│      • src/                           │    - linux               │
│      • .venv/                         │    - pentesting          │
│                                       │                           │
│  [Type your message...]               │                           │
└───────────────────────────────────────┴───────────────────────────┘
```

### 🏗️ Hackathon-Grade Layout Roadmap

To deliver a Manus.ai-quality experience, the conversational UI will adopt a three-pane architecture:

| Zone | Purpose | Key Widgets |
| --- | --- | --- |
| **Left – Ops Console** | Session metadata, node health, model routing status, quick actions (New Chat, Pin Node, Dark Mode) | Status chips, toolbelt buttons, node list with badges |
| **Center – Chat Canvas** | Context-aware dialogue with AI, inline tool call visualizations, adaptive suggestions | Chat bubbles, typing indicators, smart suggestions, slash commands |
| **Right – Intelligence Panel** | Dynamic previews (files, code, command output, sync progress) and chronological tool log | Multi-tab viewer (Preview • Tools • Timeline), file diff viewer, streaming logs |

Additional UX imperatives:

- **Context Memory Bar:** Shows the last objectives + location to keep the operator oriented.
- **Tool Trace Timeline:** Each tool call is timestamped and color-coded (success, warning, error).
- **Conversation Controls:** “New Chat”, “Summarize Session”, “Download Transcript”.
- **AI Persona Chips:** Toggle between Router AI, Execution AI, Audit AI (future multi-agent view).
- **Responsive + Themed:** Fluid layout with dark/light themes, glassmorphism cards, and keyboard shortcuts.

This blueprint guides the implementation work below.

## 🚀 Quick Start

```bash
# Make sure orchestrator is running
./scripts/start_demo_environment.sh

# Launch the conversational UI
nacc-chat

# Or with source .venv/bin/activate
source .venv/bin/activate
nacc-chat
```

Access at: **http://localhost:7860**

## 💬 Example Conversations

### 1. File Operations

**You:** "Hey, can you show me the files on the kali machine?"

**AI:** "Sure! 📂 Using **ListFiles** tool.

Here are the files on **kali-vm**:
• Desktop
• Documents
• Downloads
• nacc
• nacc-shared"

*Right panel shows: File browser with icons*

---

**You:** "Navigate to the nacc folder and show me what's inside"

**AI:** "In a moment... 📂 Using **ListFiles** and **ExecuteCommand** tools.

Folder **nacc** contains:
• node-config.yml
• src/
• .venv/
• install.sh"

*Right panel shows: Directory listing with file types*

---

**You:** "Show me the content of node-config.yml"

**AI:** "In a moment... 🔍 Using **ReadFile** tool.

Here's the content of **node-config.yml**:"

*Right panel shows: Syntax-highlighted YAML file*

---

### 2. Node Management

**You:** "Can you show me the nodes of NACC?"

**AI:** "Yes! Here are the nodes in the NACC network:

**kali-vm**
  • Status: 🟢 Online
  • Tags: kali, linux, pentesting, security, vm
  • CPU: 0.5%
  • Memory: 21.9%"

*Right panel shows: Node cards with metrics and status indicators*

---

### 3. Command Execution

**You:** "Run a network scan tool"

**AI:** "I can execute commands! Using **ExecuteCommand** tool with AI routing..."

*Right panel shows: Command output in terminal style*

---

### 4. File Transfer (Coming Soon)

**You:** "Transfer this Python file to my macOS"

**AI:** "Sharing file to macOS... 🔄 Using **SyncFiles** tool.

Transfer progress: ████████░░ 80%

Transfer complete! ✅"

*Right panel shows: Transfer progress bar*

---

## 🎯 Supported Intents

The AI understands natural language and automatically selects the right tools:

| Intent | Trigger Words | Tools Used | Right Panel |
|--------|---------------|------------|-------------|
| List Files | "show files", "list files", "what files" | `ListFiles` | File browser |
| Read File | "show content", "read file", "open file" | `ReadFile` | Syntax-highlighted code |
| Navigate | "navigate to", "go to", "cd into" | `ListFiles`, `ExecuteCommand` | Directory view |
| Show Nodes | "show nodes", "list nodes", "nodes of" | HTTP `/nodes` API | Node cards with metrics |
| Execute Command | "run", "execute", "command" | `ExecuteCommand` | Terminal output |
| Modify File | "add", "change", "edit", "update" | `WriteFile`, `ExecuteCommand` | Diff view |
| Transfer File | "share", "transfer", "copy", "send" | `SyncFiles` | Progress indicator |

## 🔧 Architecture

```
User Browser
    ↓ (WebSocket)
Gradio Interface (Port 7860)
    ↓ (HTTP/REST)
NACC Orchestrator (Port 8888)
    ↓ (MCP Protocol)
Node Servers (Kali VM, macOS, etc.)
```

## 🎨 UI Components

### Left Panel: Chat Interface
- **User messages**: Blue bubbles, right-aligned
- **AI responses**: Gray bubbles, left-aligned, markdown formatted
- **Tool indicators**: Shows which NACC tools are being used
- **Input box**: Auto-complete, enter to send

### Right Panel: Dynamic Preview
Changes based on context:
- **File Browser**: Grid of files with icons
- **Code Viewer**: Syntax-highlighted source code
- **Node Dashboard**: Cards with system metrics
- **Terminal Output**: Monospace command results
- **Transfer Progress**: Animated progress bars

## 🛠️ Customization

### Change Orchestrator URL

```bash
export NACC_ORCHESTRATOR_URL="http://your-orchestrator:8888"
nacc-chat
```

### Change Port

Edit `src/nacc_ui/conversational_ui.py`:

```python
ui.launch(
    server_name="0.0.0.0",
    server_port=9000,  # Change this
    share=False
)
```

### Enable Public Sharing

```python
ui.launch(
    server_name="0.0.0.0",
    server_port=7860,
    share=True  # Creates a public gradio.live link
)
```

## 🚦 Status Indicators

- 🟢 **Green**: Node online, operation successful
- 🔴 **Red**: Node offline, operation failed
- 🟡 **Yellow**: In progress, waiting for response
- 🔧 **Tool log**: Shows which MCP tools are being invoked

## 📱 Mobile Support

The UI is responsive and works on mobile devices:
- Touch-friendly chat bubbles
- Swipe to see right panel
- Auto-scrolling chat history

## 🎓 Pro Tips

1. **Be natural**: The AI understands conversational language
2. **Be specific**: Mention node names when targeting specific machines
3. **Check right panel**: It updates with relevant information
4. **Tool log**: Shows which NACC tools are being used behind the scenes
5. **Examples button**: Click example queries to see what's possible

## 🐛 Troubleshooting

### UI won't start
```bash
# Check if port 7860 is in use
lsof -i :7860

# Kill existing process
pkill -f nacc-chat

# Try again
nacc-chat
```

### Can't connect to orchestrator
```bash
# Verify orchestrator is running
curl http://127.0.0.1:8888/nodes

# Restart orchestrator
./scripts/start_demo_environment.sh
```

### Right panel not updating
- Refresh the browser
- Check browser console for errors
- Verify orchestrator has access to nodes

## 🌟 Future Enhancements

- [ ] Streaming responses (show AI thinking in real-time)
- [ ] File upload via drag-and-drop
- [ ] Multi-select operations (batch commands)
- [ ] Conversation history save/load
- [ ] Dark mode toggle
- [ ] Voice input support
- [ ] Collaborative sessions (multi-user)
- [ ] Custom themes

## 📄 License

Part of the NACC project. See main README for details.

---

**Built with ❤️ using Gradio and the NACC MCP protocol**
