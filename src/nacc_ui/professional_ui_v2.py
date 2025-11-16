"""
NACC Professional UI v2 - Modern Dark-Themed Enterprise Interface
Complete rewrite with clean 50/50 split layout
"""

import gradio as gr
import json
import requests
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib
import logging

# Import the existing components
from .ai_intent_parser import AIIntentParser
from .conversational_ui import NACCConversationUI, SessionState

# Orchestrator URL
ORCHESTRATOR_URL = os.getenv("NACC_ORCHESTRATOR_URL", "http://127.0.0.1:8888")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModernNACCUI(NACCConversationUI):
    """Modern redesigned UI with clean dark theme"""
    
    def __init__(self):
        super().__init__()
        
    def parse_and_enhance_response(self, result: Dict, message: str) -> str:
        """Parse orchestrator response and enhance with rich formatting"""
        bot_response = result.get("response", "")
        execution = result.get("execution", {})
        
        # Check execution results for additional context
        if execution and "results" in execution:
            exec_results = execution.get("results", [])
            if exec_results:
                first_result = exec_results[0]
                stdout = first_result.get("stdout", "").strip()
                stderr = first_result.get("stderr", "").strip()
                exit_code = first_result.get("exit_code", 0)
                
                # Enhance response based on command type
                if "install" in message.lower() and "package" in message.lower():
                    if exit_code == 0:
                        bot_response += f"\n\n✅ **Installation completed successfully!**"
                    else:
                        bot_response += f"\n\n⚠️ **Installation may have issues** (exit code: {exit_code})"
                
                if "read file" in message.lower() or "cat" in message.lower():
                    if stdout:
                        bot_response = f"📄 **File Content:**\n\n```\n{stdout}\n```"
                
                if "execute" in message.lower():
                    # Enhanced command output display
                    if stdout or stderr:
                        bot_response += f"\n\n**Output:**\n```\n{stdout if stdout else stderr}\n```"
                    if exit_code == 0:
                        bot_response += f"\n\n✅ Exit code: {exit_code}"
                    else:
                        bot_response += f"\n\n⚠️ Exit code: {exit_code}"
        
        return bot_response
    
    def handle_chat(self, message: str, history: List, session_id: str) -> Tuple[List, str, str, str, str]:
        """Handle chat messages with AI processing and enhanced response parsing"""
        if not message.strip():
            return history, "", self.get_dashboard_view(), self.list_files_view(), session_id
        
        # Get session
        session = self.get_or_create_session(session_id)
        
        # Process message
        try:
            response = requests.post(
                f"{ORCHESTRATOR_URL}/chat",
                json={
                    "query": message,
                    "session_id": session.session_id,
                    "current_node": session.current_node,
                    "current_path": session.current_path,
                    "timeout": 30
                },
                timeout=35
            )
            
            if response.status_code == 200:
                result = response.json()
                # Enhanced response parsing
                bot_response = self.parse_and_enhance_response(result, message)
                
                # Update session context
                if "context" in result:
                    session.current_node = result["context"].get("current_node", session.current_node)
                    session.current_path = result["context"].get("current_path", session.current_path)
                
            else:
                bot_response = f"⚠️ Error: {response.status_code} - {response.text}"
                
        except Exception as e:
            bot_response = f"❌ Connection error: {str(e)}"
        
        # Add to history
        history = history + [[message, bot_response]]
        
        # Update views dynamically based on current session state
        dashboard = self.get_dashboard_view(session)
        files = self.list_files_view(session.current_path, session.current_node)
        
        return history, "", dashboard, files, session_id
    
    def get_dashboard_view(self, session: Optional[SessionState] = None) -> str:
        """Get real-time network dashboard with current node highlighted"""
        # Use default values if no session
        current_node = session.current_node if session else "kali-vm"
        current_path = session.current_path if session else "/home/vasanth"
        try:
            response = requests.get(f"{ORCHESTRATOR_URL}/nodes", timeout=5)
            if response.status_code == 200:
                nodes = response.json()
                
                active = len([n for n in nodes if n.get('healthy', False)])
                total = len(nodes)
                
                dashboard = f"""🌐 **Network Dashboard**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 **System Overview**
   • Total Nodes: {total}
   • Active: {active} ✅
   • Offline: {total - active} ⚠️
   • Health Score: {(active/total*100) if total > 0 else 0:.0f}%
   
📍 **Current Node**: {current_node}
📁 **Current Path**: {current_path}

🖥️ **Connected Nodes**
"""
                for node in nodes:
                    status = "✅" if node.get('healthy') else "⚠️"
                    is_current = " ◀️ ACTIVE" if node.get('node_id') == current_node else ""
                    node_id = node.get('node_id', 'Unknown')
                    tags = ', '.join(node.get('tags', []))
                    dashboard += f"   {status} {node_id} ({tags}){is_current}\n"
                
                dashboard += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                dashboard += f"🕐 Last Updated: {datetime.now().strftime('%H:%M:%S')}\n"
                dashboard += "Status: Operational 🟢\n"
                
                return dashboard
            else:
                return "⚠️ Unable to fetch dashboard data"
        except Exception as e:
            return f"❌ Dashboard Error: {str(e)}"
    
    def list_files_view(self, path: str = "/home/vasanth", node: str = "kali-vm") -> str:
        """List files in current directory on specified node"""
        try:
            # Determine preferred tags based on node
            preferred_tags = ["mac", "local"] if node == "macbook-local" else ["kali", "vm"]
            node_label = "MacBook Pro" if node == "macbook-local" else "Kali VM"
            
            # Use orchestrator's execute command endpoint
            response = requests.post(
                f"{ORCHESTRATOR_URL}/commands/execute",
                json={
                    "description": f"List files in {path} on {node}",
                    "command": ["ls", "-lah", path],
                    "preferred_tags": preferred_tags,
                    "timeout": 10
                },
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                # Get output from first result
                results = result.get("results", [])
                if results and len(results) > 0:
                    output = results[0].get("stdout", "")
                    
                    files_view = f"""📂 **File Browser: {path}** (on {node_label})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🖥️ Node: {node}
📁 Path: {path}

{output}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
                    return files_view
                else:
                    return f"📁 **{path}**\n\nNo results from node"
            else:
                return f"📁 **{path}**\n\n⚠️ Error: {response.status_code}"
        except Exception as e:
            return f"📁 **{path}**\n\n❌ Error: {str(e)}"
    
    def execute_health_check(self) -> str:
        """Execute comprehensive health checks"""
        try:
            # Get orchestrator health
            health_response = requests.get(f"{ORCHESTRATOR_URL}/healthz", timeout=5)
            
            # Get nodes status
            nodes_response = requests.get(f"{ORCHESTRATOR_URL}/nodes", timeout=5)
            
            result = """✅ **Health Check Results**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 **System Checks**
"""
            
            # Orchestrator status
            if health_response.status_code == 200:
                result += "   • Orchestrator: ✅ Healthy\n"
            else:
                result += "   • Orchestrator: ⚠️ Degraded\n"
            
            # Nodes status
            if nodes_response.status_code == 200:
                nodes = nodes_response.json()
                result += f"   • Connected Nodes: {len(nodes)}\n\n"
                
                result += "🖥️ **Node Health**\n"
                for node in nodes:
                    node_id = node.get('node_id', 'Unknown')
                    healthy = node.get('healthy', False)
                    metrics = node.get('metrics', {})
                    
                    icon = "✅" if healthy else "⚠️"
                    result += f"   {icon} {node_id}: {'Healthy' if healthy else 'Offline'}\n"
                    
                    if healthy and metrics:
                        cpu = metrics.get('cpu_percent', 0)
                        mem = metrics.get('memory_percent', 0)
                        disk = metrics.get('disk_percent', 0)
                        result += f"      CPU: {cpu:.1f}% | Memory: {mem:.1f}% | Disk: {disk:.1f}%\n"
            else:
                result += "   • Nodes: ⚠️ Unable to fetch\n"
            
            result += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            result += "✅ All systems operational\n"
            
            return result
            
        except Exception as e:
            return f"""❌ **Health Check Failed**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Error: {str(e)}

Please ensure orchestrator is running at:
{ORCHESTRATOR_URL}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


def create_professional_ui_v2():
    """Create the modern professional UI"""
    nacc = ModernNACCUI()
    
    # Custom CSS matching dark theme
    custom_css = """
    .gradio-container {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif !important;
        background: rgb(15, 23, 42) !important;
    }
    .dark {
        background: rgb(15, 23, 42) !important;
    }
    #header {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    #header h1 {
        margin: 0;
        color: white;
        font-size: 1.75rem;
        font-weight: 700;
    }
    #header h3 {
        margin: 0.25rem 0 0 0;
        color: rgba(255, 255, 255, 0.9);
        font-size: 1rem;
        font-weight: 400;
    }
    #chat-column, #right-column {
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 12px;
        padding: 1.5rem;
        background: rgba(30, 41, 59, 0.5);
        backdrop-filter: blur(10px);
    }
    .status-bar {
        background: rgba(15, 23, 42, 0.95);
        border-top: 1px solid rgba(148, 163, 184, 0.2);
        padding: 1rem;
        font-size: 0.875rem;
        color: rgba(226, 232, 240, 0.9);
        border-radius: 8px;
        margin-top: 1rem;
    }
    .quick-actions button {
        margin: 0.25rem;
        border-radius: 8px;
        transition: all 0.2s;
    }
    .quick-actions button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    .tab-nav button {
        border-radius: 8px 8px 0 0;
    }
    /* Enhanced input styling */
    .input-row input {
        background: rgba(15, 23, 42, 0.8) !important;
        border: 2px solid rgba(148, 163, 184, 0.3) !important;
        border-radius: 10px !important;
        color: white !important;
        font-size: 1rem !important;
        padding: 0.75rem !important;
    }
    .input-row input:focus {
        border-color: rgb(59, 130, 246) !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2) !important;
    }
    .input-row input::placeholder {
        color: rgba(148, 163, 184, 0.6) !important;
    }
    /* Send button styling */
    .send-button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        min-width: 100px !important;
    }
    .send-button:hover {
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.5) !important;
    }
    /* Chatbot styling */
    .message-wrap {
        border-radius: 12px;
    }
    /* Node indicator styling */
    .node-indicator {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(37, 99, 235, 0.15) 100%) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        border-radius: 8px !important;
        padding: 0.75rem 1rem !important;
        margin-bottom: 1rem !important;
        font-size: 0.85rem !important;
    }
    .node-indicator p {
        margin: 0 !important;
        color: rgba(147, 197, 253, 1) !important;
    }
    /* Textbox output styling */
    .output-text textarea {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
        border-radius: 8px !important;
        color: rgba(226, 232, 240, 0.95) !important;
        font-family: 'SF Mono', 'Monaco', 'Consolas', monospace !important;
        font-size: 0.9rem !important;
        line-height: 1.6 !important;
        overflow-y: auto !important;
        white-space: pre !important;
        word-wrap: normal !important;
    }
    /* Theme toggle button */
    #theme-btn {
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
        color: white !important;
        min-width: 50px !important;
    }
    #theme-btn:hover {
        background: rgba(255, 255, 255, 0.2) !important;
    }
    /* Button improvements */
    button {
        transition: all 0.2s ease !important;
    }
    button:hover {
        transform: translateY(-1px) !important;
    }
    """
    
    # Build the Gradio Interface
    with gr.Blocks(
        theme=gr.themes.Soft(primary_hue="blue", secondary_hue="slate"),
        css=custom_css,
        title="NACC Enterprise AI - Professional Network Orchestration"
    ) as demo:
        
        # Session state
        session_id = gr.State()
        
        # Header Section
        with gr.Row(elem_id="header"):
            with gr.Column(scale=1):
                gr.Markdown(
                    """
                    # NACC
                    """,
                    elem_id="header-text"
                )
            with gr.Column(scale=0, min_width=100):
                theme_btn = gr.Button("🌙", size="sm", scale=0, elem_id="theme-btn")
        
        # Main Layout: 50/50 Split (Chat Left | Preview Right)
        with gr.Row(equal_height=True):
            
            # LEFT COLUMN: AI Orchestration Assistant (Chat)
            with gr.Column(scale=1, elem_id="chat-column"):
                gr.Markdown("## NACC AGENT")
                gr.Markdown("*How can I help you today?*")
                
                # Current node indicator
                with gr.Row():
                    gr.Markdown("**Active Node:** 🖥️ Kali VM | **Commands:** `list nodes`, `switch to mac`, `execute <cmd>`", 
                               elem_classes="node-indicator")
                
                chatbot = gr.Chatbot(
                    value=[],
                    height=420,  # Slightly reduced to make room for node indicator
                    show_label=False,
                    avatar_images=(None, "🤖"),
                    bubble_full_width=False,
                    show_copy_button=True
                )
                
                with gr.Row(elem_classes="input-row"):
                    msg_input = gr.Textbox(
                        placeholder="Describe your network orchestration needs...",
                        show_label=False,
                        scale=9,
                        container=False
                    )
                    send_btn = gr.Button("▶ Send", scale=1, variant="primary", elem_classes="send-button")
                
                # Example prompts as buttons
                gr.Markdown("**💡 Quick Actions:**")
                with gr.Row(elem_classes="quick-actions"):
                    ex1 = gr.Button("🖥️ Show dashboard", size="sm", variant="secondary")
                    ex2 = gr.Button("📁 List files", size="sm", variant="secondary")
                    ex3 = gr.Button("🏥 Health check", size="sm", variant="secondary")
            
            # RIGHT COLUMN: File Browser / Dashboard Preview
            with gr.Column(scale=1, elem_id="right-column"):
                
                # Tabs for different views
                with gr.Tabs(elem_classes="tab-nav"):
                    
                    # Tab 1: Dashboard
                    with gr.Tab("📊 Dashboard"):
                        dashboard_output = gr.Textbox(
                            label="Real-time Network Dashboard",
                            value=nacc.get_dashboard_view(),
                            lines=15,
                            interactive=False,
                            show_copy_button=True,
                            elem_classes="output-text"
                        )
                        refresh_dash = gr.Button("🔄 Refresh Dashboard", variant="secondary")
                    
                    # Tab 2: File Browser
                    with gr.Tab("📂 Files"):
                        current_path = gr.Textbox(
                            label="📁 Current Path",
                            value="/home/vasanth",
                            placeholder="Enter path (e.g., /home/vasanth/nacc)",
                            interactive=True,
                            max_lines=1
                        )
                        with gr.Row():
                            cd_btn = gr.Button("📂 Go to Path", variant="primary", scale=1)
                            up_btn = gr.Button("⬆️ Parent Dir", variant="secondary", scale=1)
                            refresh_btn = gr.Button("🔄 Refresh", variant="secondary", scale=1)
                        
                        file_output = gr.Textbox(
                            label="Files",
                            value=nacc.list_files_view("/home/vasanth"),
                            lines=15,
                            interactive=False,
                            show_copy_button=True,
                            elem_classes="output-text",
                            max_lines=15,
                            autoscroll=True
                        )
                    
                    # Tab 3: Help & Documentation
                    with gr.Tab("📚 Help"):
                        help_output = gr.Textbox(
                            label="About NACC Project",
                            value="""📚 ABOUT NACC PROJECT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 What is NACC?

Network AI Command & Control (NACC) is an intelligent network 
orchestration platform that combines natural language processing 
with network automation.

Simply describe what you want to accomplish, and NACC's AI will 
understand your intent and execute the appropriate commands across 
your infrastructure.

Key Features:
• Natural language interface
• Multi-node orchestration
• Real-time monitoring
• AI-powered command routing
• Context-aware sessions

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛠️ AVAILABLE TOOLS

📊 Network Dashboard
   Real-time visualization of all connected nodes with health 
   metrics, CPU/memory/disk usage, and status indicators.
   
   Try: "show dashboard" or "network status"

🖥️ Command Execution
   Execute shell commands on any node through natural language. 
   AI translates your requests into precise commands.
   
   Try: "list files in /home" or "check disk space"

📁 File Browser
   Browse, view, and manage files across your network 
   infrastructure with visual file explorer.
   
   Try: "show files" or "list directory contents"

🔍 AI Intent Parser
   Understands natural language and converts it to executable 
   commands using Mistral-NeMo 12B AI model.

🌐 Multi-Node Orchestration
   Manage multiple servers simultaneously with tag-based 
   targeting and parallel execution.

📝 Session Management
   Context-aware sessions that remember your current node, 
   path, and conversation history.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 USAGE EXAMPLES

Chat Commands:
• "Show network status" - View all nodes and their health
• "List files in /home" - Browse directory contents  
• "Show dashboard" - Display real-time metrics
• "Check system health" - Run comprehensive health checks
• "List all nodes" - Show connected infrastructure

File Operations:
• "Show files in /var/log" - Browse logs directory
• "List home directory" - View /home contents

System Monitoring:
• "What's the CPU usage?" - Check system resources
• "Show node metrics" - Display performance data
• "Network dashboard" - Real-time status overview

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏗️ ARCHITECTURE

🤖 AI Engine
   Mistral-NeMo 12B model for intent understanding and 
   command generation. Runs via Docker Desktop AI.

🚀 Orchestrator
   FastAPI-based backend managing node communication and 
   command execution at http://127.0.0.1:8888

🎨 UI Framework
   Gradio-based professional interface with dark/light 
   theme support and modern design.

🖥️ Node Agents
   Lightweight agents running on each managed server 
   (Kali VM, physical machines, containers) for command 
   execution via MCP protocol.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 GETTING STARTED

1. Start chatting with natural language commands
2. Explore the Dashboard tab for real-time metrics
3. Browse Files tab to see directory listings
4. All data is live from your connected nodes

Current Status:
✅ Orchestrator: Connected
✅ AI Engine: Active (Mistral-NeMo)
✅ Kali VM: Online and healthy

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""",
                            lines=20,
                            interactive=False,
                            elem_classes="output-text"
                        )
        
        # Status Bar at bottom
        with gr.Row():
            status = gr.Markdown(
                """
                <div class='status-bar'>
                ✅ <strong>Ready for commands</strong> | 
                🌐 Connected Nodes: Active | 
                🔒 WCAG 2.1 AA Compliant | 
                🤖 Professional AI Mode | 
                📡 Real-time Monitoring
                </div>
                """,
                elem_classes="status-bar"
            )
        
        # Event Handlers
        def send_message(msg, hist, sid):
            return nacc.handle_chat(msg, hist, sid)
        
        send_btn.click(
            fn=send_message,
            inputs=[msg_input, chatbot, session_id],
            outputs=[chatbot, msg_input, dashboard_output, file_output, session_id]
        )
        
        msg_input.submit(
            fn=send_message,
            inputs=[msg_input, chatbot, session_id],
            outputs=[chatbot, msg_input, dashboard_output, file_output, session_id]
        )
        
        # File browser navigation - SESSION AWARE
        def go_to_path(path, sid):
            session = nacc.get_or_create_session(sid)
            session.current_path = path
            return nacc.list_files_view(path, session.current_node)
        
        def go_to_parent(path, sid):
            import os
            session = nacc.get_or_create_session(sid)
            parent = os.path.dirname(path) if path != "/" else "/"
            session.current_path = parent
            return parent, nacc.list_files_view(parent, session.current_node)
        
        cd_btn.click(
            fn=go_to_path,
            inputs=[current_path, session_id],
            outputs=[file_output]
        )
        
        up_btn.click(
            fn=go_to_parent,
            inputs=[current_path, session_id],
            outputs=[current_path, file_output]
        )
        
        refresh_btn.click(
            fn=go_to_path,
            inputs=[current_path, session_id],
            outputs=[file_output]
        )
        
        ex1.click(
            fn=lambda h, s: nacc.handle_chat("Show me the real-time network dashboard", h, s),
            inputs=[chatbot, session_id],
            outputs=[chatbot, msg_input, dashboard_output, file_output, session_id]
        )
        
        ex2.click(
            fn=lambda h, s: nacc.handle_chat("List all files on the production server", h, s),
            inputs=[chatbot, session_id],
            outputs=[chatbot, msg_input, dashboard_output, file_output, session_id]
        )
        
        ex3.click(
            fn=lambda h, s: nacc.handle_chat("Execute comprehensive health checks", h, s),
            inputs=[chatbot, session_id],
            outputs=[chatbot, msg_input, dashboard_output, file_output, session_id]
        )
        
        refresh_dash.click(
            fn=nacc.get_dashboard_view,
            outputs=dashboard_output
        )
    
    return demo


def main():
    """Main entry point for the professional UI v2"""
    ui = create_professional_ui_v2()
    ui.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        favicon_path=None,
        debug=True
    )


if __name__ == "__main__":
    main()
