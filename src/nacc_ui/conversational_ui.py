"""
NACC Conversational UI - Professional ChatGPT-style interface with AI-powered tool execution
Three-pane layout:
- Left: Ops Console (nodes, tools, settings)
- Center: Chat Canvas (conversation with context)
- Right: Intelligence Panel (file preview, command output, node visualization)
"""

import gradio as gr
import json
import requests
from typing import List, Dict, Any, Optional, Tuple
import os
from pathlib import Path
from datetime import datetime
import hashlib
import logging

# Import the AI intent parser
from .ai_intent_parser import AIIntentParser, PathResolver, ExecutionPlan

# Orchestrator URL
ORCHESTRATOR_URL = os.getenv("NACC_ORCHESTRATOR_URL", "http://127.0.0.1:8888")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionState:
    """Manages conversation session state and context"""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.conversation_history: List[Dict[str, Any]] = []
        self.tool_execution_log: List[Dict[str, Any]] = []
        self.context_window_size = 10  # Last N messages for AI context
        self.current_node = "kali-vm"
        self.current_path = "/home/vasanth"
        self.created_at = datetime.now()
        
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to conversation history"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.conversation_history.append(message)
        
    def add_tool_execution(self, tool_name: str, params: Dict, result: Any, success: bool):
        """Log tool execution for debugging and context"""
        self.tool_execution_log.append({
            "tool": tool_name,
            "params": params,
            "result": result,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
        
    def get_context_window(self) -> List[Dict[str, Any]]:
        """Get recent messages for AI context"""
        return self.conversation_history[-self.context_window_size:]
    
    def clear(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.tool_execution_log = []
        

class NACCConversationUI:
    def __init__(self):
        self.sessions: Dict[str, SessionState] = {}
        self.default_node = "kali-vm"
        # Pure AI mode - no fallback heuristics
        # 30s timeout for complex network orchestration reasoning
        self.intent_parser = AIIntentParser(
            model_name="mistral-nemo", 
            timeout=30.0, 
            use_ai=True,
            use_fallback=False  # Pure AI control
        )
        
    def get_or_create_session(self, session_id: Optional[str] = None) -> SessionState:
        """Get existing session or create new one"""
        if session_id is None:
            session_id = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8]
        
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionState(session_id)
        
        return self.sessions[session_id]
    
    def get_user_home(self, node_id: str) -> str:
        """Get user home directory for a node"""
        # For now, hardcode common patterns
        # TODO: Get this from node metadata
        if "kali" in node_id.lower():
            return "/home/vasanth"
        return "/home/user"
    
    def fetch_available_nodes(self) -> List[Dict[str, Any]]:
        """Fetch available nodes from orchestrator for AI context"""
        try:
            result = self.call_orchestrator_api("/nodes", method="GET")
            if "error" not in result and "nodes" in result:
                nodes = result["nodes"]
                # Format for AI consumption
                return [
                    {
                        "node_id": node.get("node_id", "unknown"),
                        "tags": node.get("tags", []),
                        "os_type": node.get("os_type", "unknown"),
                        "status": node.get("status", "unknown"),
                        "capabilities": node.get("capabilities", [])
                    }
                    for node in nodes
                ]
            return []
        except Exception as e:
            logger.warning(f"Failed to fetch nodes: {e}")
            return []
        
    def call_orchestrator_api(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
        """Call the orchestrator API"""
        url = f"{ORCHESTRATOR_URL}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, timeout=30)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    # ============================================================================
    # Tool Registry - Maps intents to orchestrator endpoints
    # ============================================================================
    
    def tool_list_files(self, session: SessionState, path: str = None) -> Dict:
        """List files on current node"""
        target_path = path or session.current_path
        result = self.call_orchestrator_api(
            "/commands/execute",
            method="POST",
            data={
                "description": f"List files in {target_path}",
                "command": ["ls", "-la", target_path],
                "parallelism": 1
            }
        )
        session.add_tool_execution("list_files", {"path": target_path}, result, "error" not in result)
        return result
    
    def tool_read_file(self, session: SessionState, filepath: str) -> Dict:
        """Read file content"""
        result = self.call_orchestrator_api(
            "/commands/execute",
            method="POST",
            data={
                "description": f"Read file {filepath}",
                "command": ["cat", filepath],
                "parallelism": 1
            }
        )
        session.add_tool_execution("read_file", {"filepath": filepath}, result, "error" not in result)
        return result
    
    def tool_write_file(self, session: SessionState, filepath: str, content: str) -> Dict:
        """Write content to file"""
        # Using echo for simple writes; real impl should use write-file endpoint
        result = self.call_orchestrator_api(
            "/commands/execute",
            method="POST",
            data={
                "description": f"Write to file {filepath}",
                "command": ["sh", "-c", f"echo '{content}' > {filepath}"],
                "parallelism": 1
            }
        )
        session.add_tool_execution("write_file", {"filepath": filepath}, result, "error" not in result)
        return result
    
    def tool_execute_command(self, session: SessionState, description: str, command: list) -> Dict:
        """Execute arbitrary command via orchestrator"""
        result = self.call_orchestrator_api(
            "/commands/execute",
            method="POST",
            data={
                "description": description,
                "command": command,
                "parallelism": 1
            }
        )
        session.add_tool_execution("execute_command", {"command": command}, result, "error" not in result)
        return result
    
    def tool_list_nodes(self) -> Dict:
        """List all nodes in NACC network"""
        return self.call_orchestrator_api("/nodes")
    
    def tool_get_node_files(self, node_id: str, path: str = "/") -> Dict:
        """Get files from specific node"""
        return self.call_orchestrator_api(f"/nodes/{node_id}/files?path={path}")
    
    def tool_sync_files(self, source_node: str, target_nodes: List[str], strategy: str = "mirror") -> Dict:
        """Sync files between nodes"""
        return self.call_orchestrator_api(
            "/sync",
            method="POST",
            data={
                "source_node": source_node,
                "target_nodes": target_nodes,
                "strategy": strategy
            }
        )
    
    def tool_probe_ai_backend(self, message: str, context: Dict) -> Dict:
        """Probe AI backend for routing decisions"""
        return self.call_orchestrator_api(
            "/agents/probe",
            method="POST",
            data={
                "message": message,
                "context": context
            }
        )
    
    def process_message(self, user_message: str, chat_history: List, session_id: str = "default") -> Tuple[List, str, str]:
        """
        Process user message with full context awareness
        
        Returns:
            - Updated chat history
            - Right panel content (HTML)
            - Tool execution log
        """
        session = self.get_or_create_session(session_id)
        
        # Add user message to session
        session.add_message("user", user_message)
        chat_history.append({"role": "user", "content": user_message})
        
        # Get AI routing decision with full context
        ai_response, right_panel, tool_log = self.handle_intent_with_ai(user_message, session)
        
        # Add AI response to session
        session.add_message("assistant", ai_response, {"tools_used": len(session.tool_execution_log)})
        chat_history.append({"role": "assistant", "content": ai_response})
        
        return chat_history, right_panel, tool_log
    
    def handle_intent_with_ai(self, message: str, session: SessionState) -> Tuple[str, str, str]:
        """
        AI-powered intent classification and tool orchestration
        Uses AIIntentParser with Docker Mistral for precise tool execution
        
        Returns:
            - AI response text
            - Right panel HTML
            - Tool execution log
        """
        tool_log = "🤖 **AGENTIC AI**: Analyzing network orchestration request...\n"
        
        # Fetch available nodes for intelligent routing
        available_nodes = self.fetch_available_nodes()
        tool_log += f"🌐 **Available Nodes**: {len(available_nodes)} nodes discovered\n"
        
        # Build rich context for AGENTIC AI
        context = {
            "current_path": session.current_path,
            "user_home": self.get_user_home(session.current_node),
            "current_node": session.current_node,
            "os_type": "linux",  # TODO: Get from node metadata
            "available_nodes": available_nodes,  # NEW: Network awareness
            "conversation_history": [
                {"role": msg["role"], "content": msg["content"][:100]}
                for msg in session.get_context_window()
            ],
            "recent_tools": session.tool_execution_log[-3:] if session.tool_execution_log else []
        }
        
        # Use AI intent parser
        try:
            execution_plan = self.intent_parser.parse(message, context)
            
            tool_log += f"\n📋 **Intent**: {execution_plan.intent}\n"
            tool_log += f"🖥️  **Target Node**: {execution_plan.target_node or 'auto-select'}\n"
            tool_log += f"⚡ **Strategy**: {execution_plan.execution_strategy}\n"
            tool_log += f"🎯 **Path**: {execution_plan.target_path or 'N/A'}\n"
            tool_log += f"💪 **Confidence**: {execution_plan.confidence:.0%}\n"
            tool_log += f"🧠 **Reasoning**: {execution_plan.reasoning}\n"
            tool_log += f"🔧 **Tools**: {len(execution_plan.tools)} tool(s)\n\n"
            
            # Execute the plan
            ai_response, right_panel = self._execute_plan(execution_plan, session, tool_log)
            
            return ai_response, right_panel, tool_log
            
        except Exception as e:
            logger.error(f"AI intent parsing failed: {e}")
            tool_log += f"⚠️ Error: {str(e)}\n"
            tool_log += "Falling back to pattern matching...\n"
            
            # Fallback to old pattern matching
            ai_response, right_panel = self._route_with_patterns(message, session, tool_log)
            return ai_response, right_panel, tool_log
    
    def _execute_plan(self, plan: ExecutionPlan, session: SessionState, tool_log: str) -> Tuple[str, str]:
        """
        Execute the AI's structured plan
        
        Returns:
            - AI response text
            - Right panel HTML
        """
        ai_response = ""
        right_panel = ""
        
        # Execute each tool in order
        for tool_call in plan.tools:
            tool_name = tool_call.tool_name
            params = tool_call.parameters
            
            logger.info(f"Executing tool: {tool_name} with params: {params}")
            
            if tool_name == "write_file":
                # Create file
                filepath = params.get("filepath")
                content = params.get("content", "")
                
                result = self.tool_write_file(session, filepath, content)
                
                if "error" not in result or result.get("results", [{}])[0].get("exit_code") == 0:
                    ai_response = f"✅ **File created successfully!**\n\nCreated `{Path(filepath).name}` in `{Path(filepath).parent}`\n\nContent:\n```\n{content}\n```"
                    right_panel = f"""
                    <div style="padding: 20px; font-family: 'Inter', sans-serif;">
                        <h3 style="color: #10b981;">✅ File Created Successfully</h3>
                        <div style="background: #f0fdf4; border-left: 4px solid #10b981; padding: 15px; border-radius: 8px; margin-top: 15px;">
                            <div style="font-weight: 600; margin-bottom: 10px;">📄 {Path(filepath).name}</div>
                            <div style="color: #6b7280; font-size: 14px;">Path: {filepath}</div>
                            <div style="color: #6b7280; font-size: 14px;">Size: {len(content)} bytes</div>
                        </div>
                        <div style="background: #1e293b; border-radius: 8px; padding: 15px; margin-top: 15px; overflow: auto;">
                            <pre style="margin: 0; color: #e2e8f0; font-family: 'Monaco', monospace; font-size: 13px;">{content}</pre>
                        </div>
                    </div>
                    """
                else:
                    ai_response = f"❌ Failed to create file: {result.get('error', 'Unknown error')}"
                    right_panel = f"<div class='error'>Error: {result.get('error')}</div>"
            
            elif tool_name == "list_files":
                # List directory
                path = params.get("path", session.current_path)
                session.current_path = path  # Update session
                
                result = self.tool_list_files(session, path)
                
                if "error" not in result and "results" in result:
                    stdout = result["results"][0].get("stdout", "")
                    lines = stdout.strip().split("\n")[1:]  # Skip total line
                    files = []
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 9:
                            filename = " ".join(parts[8:])
                            if parts[0].startswith('d'):
                                files.append(filename + "/")
                            else:
                                files.append(filename)
                    
                    file_list = "\n".join([f"• {f}" for f in files])
                    ai_response = f"📂 **Directory Contents**: `{path}`\n\n{file_list}\n\n✅ Found {len(files)} items"
                    right_panel = self.render_file_browser(files, path)
                else:
                    ai_response = f"❌ Failed to list files: {result.get('error', 'Unknown error')}"
                    right_panel = f"<div class='error'>Error: {result.get('error')}</div>"
            
            elif tool_name == "read_file":
                # Read file
                filepath = params.get("filepath")
                result = self.tool_read_file(session, filepath)
                
                if "error" not in result and "results" in result:
                    stdout = result["results"][0].get("stdout", "")
                    exit_code = result["results"][0].get("exit_code", 1)
                    
                    if exit_code == 0 and stdout:
                        ai_response = f"📄 **File Contents**: `{Path(filepath).name}`\n\n```\n{stdout[:500]}{'...' if len(stdout) > 500 else ''}\n```"
                        right_panel = self.render_file_content(Path(filepath).name, stdout)
                    else:
                        ai_response = f"❌ Could not read file: {filepath}"
                        right_panel = f"<div class='error'>File not found or not readable</div>"
                else:
                    ai_response = f"❌ Error reading file: {result.get('error', 'Unknown error')}"
                    right_panel = f"<div class='error'>Error: {result.get('error')}</div>"
        
        return ai_response, right_panel
    
    def _route_with_patterns(self, message: str, session: SessionState, tool_log_prefix: str) -> Tuple[str, str]:
        """
        Enhanced pattern-based routing with session context
        
        Returns:
            - AI response text
            - Right panel HTML
        """
        message_lower = message.lower()
        tool_log = tool_log_prefix
        right_panel = ""
        
        # Intent: List files
        if any(word in message_lower for word in ["show files", "list files", "files on", "what files"]):
            tool_log += "🔧 Using tool: list_files\n"
            
            # Use tool_list_files with session context
            result = self.tool_list_files(session)
            
            if "error" not in result and "results" in result:
                stdout = result["results"][0].get("stdout", "")
                # Parse ls output
                lines = stdout.strip().split("\n")[1:]  # Skip total line
                files = []
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 9:
                        filename = " ".join(parts[8:])
                        if parts[0].startswith('d'):
                            files.append(filename + "/")
                        else:
                            files.append(filename)
                
                file_list = "\n".join([f"• {f}" for f in files])
                ai_response = f"Sure! 📂 Using **list_files** tool.\n\nHere are the files on **{session.current_node}** at `{session.current_path}`:\n\n{file_list}"
                
                # Right panel: File browser view
                right_panel = self.render_file_browser(files, session.current_path)
            else:
                error_msg = result.get("error", "Unknown error")
                ai_response = f"Sorry, I encountered an error: {error_msg}"
                right_panel = f"<div class='error'>Error: {error_msg}</div>"
        
        # Intent: Navigate to directory / Read file
        elif any(word in message_lower for word in ["navigate to", "go to", "open", "show me the", "file content", "show content"]):
            # Extract filename (simple pattern matching)
            words = message.split()
            filename = None
            for i, word in enumerate(words):
                if word.lower() in ["file", "to", "folder", "directory"] and i + 1 < len(words):
                    filename = words[i + 1].strip('.,!?')
                    break
            
            # Also try to extract names in quotes or after common prepositions
            if not filename:
                for i, word in enumerate(words):
                    if word.lower() in ["nacc", "config", "node-config.yml", "src", "Documents"]:
                        filename = word
                        break
            
            if filename:
                tool_log += f"🔧 Using tools: read_file\n"
                
                # Build full path
                full_path = f"{session.current_path}/{filename}" if not filename.startswith("/") else filename
                
                # Try to read as file first
                read_result = self.tool_read_file(session, full_path)
                
                if "error" not in read_result and "results" in read_result:
                    stdout = read_result["results"][0].get("stdout", "")
                    exit_code = read_result["results"][0].get("exit_code", 1)
                    
                    if exit_code == 0 and stdout:
                        # It's a file!
                        ai_response = f"Got it! 🔍 Using **read_file** tool.\n\nHere's the content of **{filename}**:"
                        right_panel = self.render_file_content(filename, stdout)
                    else:
                        # Try listing as directory
                        session.current_path = full_path  # Update session path
                        list_result = self.tool_list_files(session, full_path)
                        
                        if "error" not in list_result and "results" in list_result:
                            stdout = list_result["results"][0].get("stdout", "")
                            lines = stdout.strip().split("\n")[1:]  # Skip total line
                            files = []
                            for line in lines:
                                parts = line.split()
                                if len(parts) >= 9:
                                    fname = " ".join(parts[8:])
                                    if parts[0].startswith('d'):
                                        files.append(fname + "/")
                                    else:
                                        files.append(fname)
                            
                            file_list = "\n".join([f"• {f}" for f in files])
                            ai_response = f"Navigating... 📂 Using **list_files** tool.\n\nFolder **{filename}** contains:\n\n{file_list}"
                            right_panel = self.render_file_browser(files, full_path)
                        else:
                            ai_response = f"Sorry, couldn't access **{filename}**"
                            right_panel = f"<div class='error'>Could not access {filename}</div>"
                else:
                    ai_response = f"Sorry, couldn't read **{filename}**"
                    right_panel = f"<div class='error'>Error reading file</div>"
            else:
                ai_response = "Could you specify which file or folder you want to navigate to?"
                right_panel = ""
        
        # Intent: Transfer file
        elif any(word in message_lower for word in ["share", "transfer", "copy", "send", "sync"]):
            tool_log += "🔧 Using tool: sync_files\n"
            
            # Extract target nodes (simplified)
            target_nodes = []
            if "macos" in message_lower:
                target_nodes.append("macos-node")
            if "kali" in message_lower:
                target_nodes.append("kali-vm")
            
            if target_nodes:
                result = self.tool_sync_files(session.current_node, target_nodes)
                if "error" not in result:
                    ai_response = f"Perfect! � Using **sync_files** tool.\n\nSyncing files from **{session.current_node}** to {', '.join(target_nodes)}..."
                    right_panel = f"<div class='success'>Sync initiated to {len(target_nodes)} node(s)</div>"
                else:
                    ai_response = f"Sync encountered an error: {result.get('error')}"
                    right_panel = f"<div class='error'>{result.get('error')}</div>"
            else:
                ai_response = "I can sync files between nodes! Which node would you like to sync to?"
                right_panel = "<div class='info'>Specify target node for sync</div>"
        
        # Intent: Show nodes
        elif any(word in message_lower for word in ["show nodes", "list nodes", "nodes of", "what nodes"]):
            tool_log += "🔧 Using tool: list_nodes\n"
            result = self.tool_list_nodes()
            
            if "error" not in result and isinstance(result, list):
                ai_response = "Yes! Here are the nodes in the NACC network:\n\n"
                for node in result:
                    node_id = node.get('node_id') or node.get('id', 'Unknown')
                    ai_response += f"**{node_id}**\n"
                    ai_response += f"  • Status: {'🟢 Online' if node.get('healthy') else '🔴 Offline'}\n"
                    ai_response += f"  • Tags: {', '.join(node.get('tags', []))}\n"
                    metrics = node.get('metrics', {})
                    if metrics:
                        ai_response += f"  • CPU: {metrics.get('cpu_percent', 0):.1f}%\n"
                        ai_response += f"  • Memory: {metrics.get('memory_percent', 0):.1f}%\n"
                    ai_response += "\n"
                
                right_panel = self.render_nodes_view(result)
            else:
                ai_response = "Sorry, couldn't fetch nodes information."
                right_panel = "<div class='error'>Error fetching nodes</div>"
        
        # Intent: Execute command
        elif any(word in message_lower for word in ["run", "execute", "command"]):
            tool_log += "🔧 Using tool: execute_command\n"
            # Try to extract command from message
            ai_response = "I can execute commands! What command would you like me to run?\n\nExample: 'run ls -la' or 'execute whoami'"
            right_panel = "<div class='info'>Ready to execute commands on " + session.current_node + "</div>"
        
        # Intent: Modify file
        elif any(word in message_lower for word in ["add", "modify", "change", "edit", "update", "write"]):
            tool_log += "🔧 Using tool: write_file\n"
            # Extract filename and content (simplified)
            ai_response = "I can modify files! Please specify:\n\n• Which file to edit\n• What changes to make\n\nExample: 'Add a print statement to app.py'"
            right_panel = "<div class='info'>Ready to modify files</div>"
        
        # Default: General chat with context awareness
        else:
            # Show context-aware help
            context_hint = ""
            if session.conversation_history:
                context_hint = f"\n\n💡 Current context:\n• Node: **{session.current_node}**\n• Path: `{session.current_path}`\n• Tools used: {len(session.tool_execution_log)}"
            
            ai_response = f"I'm NACC AI! 🤖 I can help you:\n\n• 📂 Browse files across nodes\n• 📝 Read and modify files\n• 🔄 Transfer files between machines\n• 💻 Execute commands\n• 🌐 Manage nodes{context_hint}\n\nWhat would you like to do?"
            right_panel = self.render_welcome_panel()
        
        return ai_response, right_panel
    
    def render_file_browser(self, files: List[str], current_path: str) -> str:
        """Render file browser in right panel"""
        html = f"""
        <div style="padding: 20px; font-family: 'Inter', sans-serif;">
            <h3 style="color: #1f2937; margin-bottom: 10px;">📂 {current_path}</h3>
            <div style="background: #f9fafb; border-radius: 8px; padding: 15px; border: 1px solid #e5e7eb;">
        """
        
        for file in files:
            icon = "📁" if "/" in file or not "." in file else "📄"
            html += f"""
                <div style="padding: 8px; margin: 5px 0; background: white; border-radius: 6px; border: 1px solid #e5e7eb; cursor: pointer; transition: all 0.2s;">
                    {icon} <span style="font-family: 'Monaco', monospace; color: #374151;">{file}</span>
                </div>
            """
        
        html += "</div></div>"
        return html
    
    def render_file_content(self, filename: str, content: str) -> str:
        """Render file content in right panel"""
        # Detect language from extension
        ext = Path(filename).suffix
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".sh": "bash",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".json": "json",
            ".md": "markdown"
        }
        lang = lang_map.get(ext, "text")
        
        html = f"""
        <div style="padding: 20px; font-family: 'Inter', sans-serif;">
            <h3 style="color: #1f2937; margin-bottom: 10px;">📄 {filename}</h3>
            <div style="background: #1e293b; border-radius: 8px; padding: 20px; overflow: auto; max-height: 600px;">
                <pre style="margin: 0; color: #e2e8f0; font-family: 'Monaco', 'Courier New', monospace; font-size: 13px; line-height: 1.6;"><code class="language-{lang}">{content}</code></pre>
            </div>
        </div>
        """
        return html
    
    def render_nodes_view(self, nodes: List[Dict]) -> str:
        """Render nodes visualization in right panel"""
        html = """
        <div style="padding: 20px; font-family: 'Inter', sans-serif;">
            <h3 style="color: #1f2937; margin-bottom: 15px;">🌐 NACC Network Nodes</h3>
        """
        
        for node in nodes:
            node_id = node.get('node_id') or node.get('id', 'Unknown')
            is_healthy = node.get('healthy', False)
            status_color = "#10b981" if is_healthy else "#ef4444"
            metrics = node.get('metrics', {})
            
            html += f"""
            <div style="background: white; border-radius: 12px; padding: 20px; margin-bottom: 15px; border-left: 4px solid {status_color}; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <h4 style="margin: 0; color: #1f2937; font-size: 18px;">🖥️ {node_id}</h4>
                    <span style="background: {status_color}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;">
                        {'ONLINE' if is_healthy else 'OFFLINE'}
                    </span>
                </div>
                <div style="color: #6b7280; font-size: 14px; line-height: 1.8;">
                    <div>🏷️ <strong>Tags:</strong> {', '.join(node.get('tags', []))}</div>
            """
            
            if metrics:
                html += f"""
                    <div>💻 <strong>CPU:</strong> {metrics.get('cpu_percent', 0):.1f}%</div>
                    <div>💾 <strong>Memory:</strong> {metrics.get('memory_percent', 0):.1f}%</div>
                    <div>� <strong>Disk:</strong> {metrics.get('disk_percent', 0):.1f}%</div>
                """
            
            html += """
                </div>
            </div>
            """
        
        html += "</div>"
        return html
    
    def render_welcome_panel(self) -> str:
        """Render welcome panel"""
        return """
        <div style="padding: 40px; text-align: center; font-family: 'Inter', sans-serif;">
            <h2 style="color: #1f2937; margin-bottom: 20px;">🚀 Welcome to NACC AI</h2>
            <p style="color: #6b7280; font-size: 16px; line-height: 1.8; max-width: 500px; margin: 0 auto;">
                Network Agentic Connection Call with AI-powered orchestration
            </p>
            <div style="margin-top: 40px; display: grid; gap: 15px;">
                <div style="background: #f0fdf4; border: 1px solid #86efac; border-radius: 8px; padding: 15px;">
                    <div style="font-size: 24px; margin-bottom: 5px;">📂</div>
                    <div style="color: #166534; font-weight: 600;">File Operations</div>
                </div>
                <div style="background: #eff6ff; border: 1px solid #93c5fd; border-radius: 8px; padding: 15px;">
                    <div style="font-size: 24px; margin-bottom: 5px;">💻</div>
                    <div style="color: #1e40af; font-weight: 600;">Command Execution</div>
                </div>
                <div style="background: #fef3c7; border: 1px solid #fcd34d; border-radius: 8px; padding: 15px;">
                    <div style="font-size: 24px; margin-bottom: 5px;">🌐</div>
                    <div style="color: #92400e; font-weight: 600;">Node Management</div>
                </div>
            </div>
        </div>
        """


def create_ui():
    """Create the Gradio UI"""
    nacc = NACCConversationUI()
    
    # Custom CSS for professional Manus-style look
    css = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .gradio-container {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    }
    
    .chat-message {
        padding: 14px 18px !important;
        border-radius: 16px !important;
        margin-bottom: 10px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
        transition: all 0.2s ease !important;
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        margin-left: 15% !important;
        border-bottom-right-radius: 4px !important;
    }
    
    .bot-message {
        background: white !important;
        color: #1f2937 !important;
        margin-right: 15% !important;
        border-bottom-left-radius: 4px !important;
        border-left: 3px solid #667eea !important;
    }
    
    #chat-input {
        border-radius: 12px !important;
        border: 2px solid #e5e7eb !important;
        padding: 14px 20px !important;
        font-size: 15px !important;
        transition: all 0.2s ease !important;
    }
    
    #chat-input:focus {
        border-color: #667eea !important;
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    .tool-log {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%) !important;
        border-left: 4px solid #f59e0b !important;
        padding: 14px !important;
        border-radius: 8px !important;
        font-family: 'Monaco', 'Courier New', monospace !important;
        font-size: 13px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08) !important;
        margin-top: 10px !important;
    }
    
    .context-bar {
        background: linear-gradient(135deg, #e0e7ff 0%, #ddd6fe 100%) !important;
        border-left: 4px solid #667eea !important;
        padding: 12px 16px !important;
        border-radius: 8px !important;
        font-size: 13px !important;
        margin-top: 8px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06) !important;
    }
    
    button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    
    button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
    }
    
    .gradio-row {
        gap: 16px !important;
    }
    
    .gradio-column {
        background: white !important;
        border-radius: 16px !important;
        padding: 24px !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1) !important;
    }
    """
    
    with gr.Blocks(css=css, title="NACC AI - Professional Orchestration Interface", theme=gr.themes.Soft()) as interface:
        gr.Markdown(
            """
            # 🤖 NACC AI - Network Orchestration Assistant
            ### Context-Aware Conversational Interface with Multi-Tool Execution
            Professional AI-powered distributed systems management
            """
        )
        
        # Session state (stored in Gradio state)
        session_id_state = gr.State(value=None)
        
        with gr.Row():
            # Left side: Chat interface with session controls
            with gr.Column(scale=1):
                with gr.Row():
                    gr.Markdown("### 💬 Chat with NACC AI")
                    new_chat_btn = gr.Button("🔄 New Chat", size="sm", variant="secondary", scale=0)
                
                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=550,
                    show_label=False,
                    type="messages"
                )
                
                with gr.Row():
                    msg = gr.Textbox(
                        label="Message",
                        placeholder="Type your message... (e.g., 'show me files on kali machine')",
                        show_label=False,
                        container=False,
                        elem_id="chat-input",
                        scale=9
                    )
                    submit = gr.Button("📤", variant="primary", scale=1, min_width=50)
                
                tool_log = gr.Markdown(
                    "🚀 Ready to assist! Context-aware AI routing active.",
                    elem_classes=["tool-log"]
                )
                
                # Context info bar
                context_bar = gr.Markdown(
                    "💡 **Context:** New session | No tools executed yet",
                    elem_classes=["context-bar"]
                )
            
            # Right side: Preview/Output panel
            with gr.Column(scale=1):
                right_panel = gr.HTML(
                    nacc.render_welcome_panel(),
                    label="📊 Preview & Output"
                )
        
        # Example queries
        gr.Markdown("### 💡 Try these examples:")
        with gr.Row():
            gr.Examples(
                examples=[
                    ["Hey, can you show me the files on the kali machine?"],
                    ["Navigate to file A and share the contents to me"],
                    ["Can you show me the nodes of NACC?"],
                    ["Add a print statement to the Python file"],
                    ["Transfer this file to my macOS"]
                ],
                inputs=msg
            )
        
        def respond(message, chat_history, session_id):
            """Handle user message with session context"""
            if not message.strip():
                return "", chat_history, gr.update(), gr.update(), gr.update(), session_id
            
            updated_history, right_content, log = nacc.process_message(message, chat_history or [], session_id)
            
            # Update context bar
            session = nacc.get_or_create_session(session_id)
            context_info = (
                f"💡 **Context:** Session `{session.session_id[:6]}...` | "
                f"Node: `{session.current_node}` | Path: `{session.current_path}` | "
                f"Tools executed: {len(session.tool_execution_log)} | "
                f"Messages: {len(session.conversation_history)}"
            )
            
            return "", updated_history, right_content, log, context_info, session_id
        
        def new_chat(session_id):
            """Start a new chat session"""
            # Generate new session ID
            import hashlib
            from datetime import datetime
            new_session_id = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8]
            
            return [], nacc.render_welcome_panel(), "🚀 New chat started! Context-aware AI routing active.", "💡 **Context:** New session | No tools executed yet", new_session_id
        
        # Event handlers
        submit.click(
            respond, 
            [msg, chatbot, session_id_state], 
            [msg, chatbot, right_panel, tool_log, context_bar, session_id_state]
        )
        msg.submit(
            respond, 
            [msg, chatbot, session_id_state], 
            [msg, chatbot, right_panel, tool_log, context_bar, session_id_state]
        )
        new_chat_btn.click(
            new_chat,
            [session_id_state],
            [chatbot, right_panel, tool_log, context_bar, session_id_state]
        )
    
    return interface


def main():
    """Main entry point for the CLI"""
    ui = create_ui()
    ui.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )

if __name__ == "__main__":
    main()
