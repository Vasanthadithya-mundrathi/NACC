"""FastAPI application exposing orchestrator capabilities."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .config import load_orchestrator_config
from .service import OrchestratorService


class ListFilesPayload(BaseModel):
    path: str = "."
    recursive: bool = False
    pattern: str | None = None
    include_hash: bool = False


class CommandPayload(BaseModel):
    description: str = Field(..., description="Human-readable summary of the command")
    command: list[str] | str
    preferred_tags: list[str] | None = None
    parallelism: int = Field(default=1, ge=1, le=8)
    timeout: float | None = Field(default=None, gt=0.0, le=600.0)
    cwd: str | None = None
    env: dict[str, str] | None = None


class SyncPayload(BaseModel):
    source_node: str
    source_path: str
    target_nodes: list[str]
    strategy: str = Field(default="mirror")


class ProbePayload(BaseModel):
    message: str = Field(default="Ping from NACC UI")
    context: dict[str, Any] | None = None


class ChatPayload(BaseModel):
    query: str = Field(..., description="User's natural language query")
    session_id: str = Field(default="default")
    current_node: str | None = None
    current_path: str = Field(default="/home")
    timeout: float = Field(default=30.0, gt=0.0, le=600.0)


def build_service(config_path: str | None = None) -> OrchestratorService:
    config = load_orchestrator_config(config_path or "orchestrator-config.yml")
    return OrchestratorService(config)


def create_app(service: OrchestratorService) -> FastAPI:
    app = FastAPI(title="NACC Orchestrator", version="0.4.0")

    @app.get("/healthz")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/nodes")
    def list_nodes() -> list[dict[str, object]]:
        return service.list_nodes()

    @app.get("/nodes/{node_id}")
    def node_info(node_id: str) -> dict[str, object]:
        try:
            return service.get_node_info(node_id)
        except KeyError as exc:  # pragma: no cover - FastAPI error path
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/nodes/{node_id}/files")
    def list_files(node_id: str, payload: ListFilesPayload) -> dict[str, object]:
        return service.list_files(
            node_id,
            path=payload.path,
            recursive=payload.recursive,
            pattern=payload.pattern,
            include_hash=payload.include_hash,
        )

    @app.post("/commands/execute")
    def execute_command(payload: CommandPayload) -> dict[str, object]:
        return service.execute_command(
            description=payload.description,
            command=payload.command,
            preferred_tags=payload.preferred_tags,
            parallelism=payload.parallelism,
            timeout=payload.timeout,
            cwd=payload.cwd,
            env=payload.env,
        )

    @app.post("/sync")
    def sync(payload: SyncPayload) -> dict[str, object]:
        return service.sync_path(
            payload.source_node,
            source_path=payload.source_path,
            target_nodes=payload.target_nodes,
            strategy=payload.strategy,
        )

    @app.post("/agents/probe")
    def probe_backend(payload: ProbePayload) -> dict[str, object]:
        return service.check_agent_backend(payload.message, payload.context)

    @app.post("/chat")
    def chat(payload: ChatPayload) -> dict[str, object]:
        """Handle natural language chat queries with AI-powered tool calling"""
        try:
            context = {
                "session_id": payload.session_id,
                "current_node": payload.current_node or "kali-vm",
                "current_path": payload.current_path or "/home/vasanth"
            }
            
            # Define available tools with clear descriptions
            tools = {
                "switch_node": {
                    "description": "Switch to a different node (mac/macbook/local for Mac, kali/vm for Kali VM)",
                    "parameters": ["target_node"],
                    "examples": ["switch to mac", "use kali node", "go to macbook"]
                },
                "list_nodes": {
                    "description": "List all available nodes with their status and metrics",
                    "parameters": [],
                    "examples": ["show nodes", "list all nodes", "available nodes"]
                },
                "list_files": {
                    "description": "List files in current or specified directory",
                    "parameters": ["path (optional)"],
                    "examples": ["list files", "ls", "show files in /home"]
                },
                "change_directory": {
                    "description": "Navigate to a different directory",
                    "parameters": ["path"],
                    "examples": ["cd /home", "go to documents", "navigate to downloads"]
                },
                "write_file": {
                    "description": "Create or write content to a file",
                    "parameters": ["file_name", "content"],
                    "examples": ["create file test.txt with content hello", "write hello to test.txt", "make a file named data.json"]
                },
                "read_file": {
                    "description": "Read and display the contents of a file",
                    "parameters": ["file_name"],
                    "examples": ["read test.txt", "show contents of config.yml", "cat data.json", "display file.txt"]
                },
                "delete_file": {
                    "description": "Delete a file from the filesystem",
                    "parameters": ["file_name"],
                    "examples": ["delete test.txt", "remove file.txt", "rm data.json", "delete the file config.yml"]
                },
                "sync_files": {
                    "description": "Share or sync files between nodes (e.g., from Kali to Mac)",
                    "parameters": ["source_path", "target_nodes"],
                    "examples": ["share test.txt from kali-vm to macbook-local", "sync file.txt to mac", "copy data.json from kali to macbook"]
                },
                "execute_command": {
                    "description": "Execute a shell command on current node",
                    "parameters": ["command"],
                    "examples": ["execute ls -la", "run whoami", "exec pwd"]
                },
                "install_package": {
                    "description": "Install a package using apt (Kali) or brew (Mac)",
                    "parameters": ["package_name"],
                    "examples": ["install cowsay", "apt install nmap", "brew install wget"]
                },
                "get_status": {
                    "description": "Show system status and node health metrics",
                    "parameters": [],
                    "examples": ["status", "show dashboard", "health check", "system info"]
                }
            }
            
            # Build AI prompt with tool definitions
            tool_descriptions = "\n".join([
                f"- {name}: {tool['description']}"
                for name, tool in tools.items()
            ])
            
            ai_prompt = f"""You are an intelligent orchestrator assistant. Analyze the user's query and determine which tool(s) to use.
            
            CRITICAL INSTRUCTIONS:
            1. If the user wants to SEE content, use "read_file". DO NOT use "write_file".
            2. If the user wants to REMOVE a file, use "delete_file". DO NOT use "write_file".
            3. If the user wants to COPY/SHARE files between nodes, use "sync_files".
            4. Only use "write_file" if the user explicitly asks to CREATE or WRITE content.
            
            Available Tools:
            {tool_descriptions}
            
            Current Context:
            - Node: {context['current_node']}
            - Path: {context['current_path']}
            
            User Query: {payload.query}
            
            Respond with a JSON object containing:
            {{
                "tool": "<tool_name>",
                "parameters": {{"param1": "value1", ...}},
                "reasoning": "<brief explanation>"
            }}
            
            If the query doesn't match any tool, set "tool" to "general_response" and include your response in "reasoning"."""
            
            # Get AI decision
            ai_result = service.check_agent_backend(ai_prompt, context)
            ai_response = ai_result.get("response", "")
            
            # Try to parse AI's structured response
            import json
            import re
            
            tool_call = None
            try:
                # Try to parse AI's structured response
                # Use greedy match to handle nested braces
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    tool_call = json.loads(json_match.group(0))
            except:
                pass
            
            # Fallback: Use simple keyword matching if AI fails
            query_lower = payload.query.lower()
            
            # Determine tool using AI if available, otherwise use keywords
            tool_name = tool_call.get("tool") if tool_call else None
            parameters = tool_call.get("parameters", {}) if tool_call else {}
            reasoning = tool_call.get("reasoning", "") if tool_call else ""
            
            # Enhanced parameter extraction from query using regex patterns
            def extract_filename_and_content(query: str) -> tuple[str | None, str | None]:
                filename = None
                content = None
                
                # Pattern 1: "create file <filename> with content <content>"
                match = re.search(r'create file\s+([^\s]+)\s+with content\s+(.+)', query, re.IGNORECASE)
                if match:
                    filename = match.group(1)
                    content = match.group(2)
                    return filename, content
                
                # Pattern 2: "write <content> to <filename>"
                match = re.search(r'write\s+(.+)\s+to\s+([^\s]+)', query, re.IGNORECASE)
                if match:
                    content = match.group(1)
                    filename = match.group(2)
                    return filename, content
                
                # Pattern 3: "create <filename>" or "make <filename>"
                match = re.search(r'(?:create|make)\s+(?:file\s+)?([^\s]+)', query, re.IGNORECASE)
                if match:
                    filename = match.group(1)
                    return filename, content # Content will be None
                
                return None, None
            
            # ===== NODE MANAGEMENT =====
            
            # Switch node
            # Switch node
            if tool_name == "switch_node" or any(word in query_lower for word in ["switch to", "use node", "change node", "go to"]):
                import re
                
                # Extract target node from query
                target_node = None
                
                # 1. Try to find exact node ID match from registry
                available_nodes = service.list_nodes()
                for node in available_nodes:
                    node_id = node.get('node_id')
                    if node_id and node_id.lower() in query_lower:
                        target_node = node_id
                        break
                
                # 2. Fallback: Check for common aliases if no exact ID match
                if not target_node:
                    if any(word in query_lower for word in ["mac", "macbook", "local", "host"]):
                        # Try to find a node with 'mac' tag
                        for node in available_nodes:
                            if "mac" in node.get('tags', []) or "macos" in node.get('tags', []):
                                target_node = node.get('node_id')
                                break
                    elif "kali" in query_lower or "vm" in query_lower:
                        # Try to find a node with 'kali' tag
                        for node in available_nodes:
                            if "kali" in node.get('tags', []) or "vm" in node.get('tags', []):
                                target_node = node.get('node_id')
                                break
                
                if target_node:
                    context["current_node"] = target_node
                    context["current_path"] = "~" # Reset to home directory
                    
                    return {
                        "response": f"✅ **Switched to node: {target_node}**\n\n📍 Current path: `~`",
                        "context": context
                    }
                else:
                     return {
                        "response": f"❌ Could not find specified node. Available nodes: {', '.join([n.get('node_id') for n in available_nodes])}",
                        "context": context
                    }
            
            # List all nodes
            if tool_name == "list_nodes" or any(word in query_lower for word in ["list nodes", "show nodes", "all nodes", "available nodes"]):
                nodes = service.list_nodes()
                response = "🌐 **Available Nodes:**\n\n"
                for node in nodes:
                    node_id = node.get('node_id', 'Unknown')
                    healthy = node.get('healthy', False)
                    status = "✅ Online" if healthy else "⚠️ Offline"
                    current = "← CURRENT" if node_id == context["current_node"] else ""
                    response += f"• **{node_id}**: {status} {current}\n"
                    if healthy:
                        metrics = node.get('metrics', {})
                        if metrics:
                            cpu = metrics.get('cpu_percent', 0)
                            mem = metrics.get('memory_percent', 0)
                            response += f"  CPU: {cpu:.1f}% | Memory: {mem:.1f}%\n"
                
                return {"response": response, "context": context}
            
            # Connect/Pair node using pairing code
            if any(word in query_lower for word in ["connect to", "pair with", "register node"]):
                import re
                import uuid
                from .config import NodeDefinition
                
                # Extract code and name
                # Pattern: "connect to 123456 and name it as my-laptop"
                code_match = re.search(r'(?:connect to|pair with|code)\s+([0-9]{6})', query_lower)
                name_match = re.search(r'(?:name it as|call it|name)\s+([a-zA-Z0-9_-]+)', query_lower)
                ip_match = re.search(r'(?:at|ip)\s+([\d.]+)', query_lower)
                
                if code_match:
                    pairing_code = code_match.group(1)
                    node_name = name_match.group(1) if name_match else f"Node-{pairing_code}"
                    node_ip = ip_match.group(1) if ip_match else None
                    
                    if not node_ip:
                        return {
                            "response": f"❌ Please specify the IP address of the node.\n\nExample: `connect to {pairing_code} at 192.168.1.50 and name it as {node_name}`",
                            "context": context
                        }
                    
                    try:
                        # Create new node definition (same logic as CLI)
                        # Use name as ID if possible, otherwise generate UUID
                        if node_name and re.match(r'^[a-zA-Z0-9_-]+$', node_name):
                            node_id = node_name
                        else:
                            node_id = str(uuid.uuid4())[:8]  # Short UUID
                        
                        # Intelligently detect tags based on node name and IP
                        tags = ["dynamic", "paired"]
                        node_name_lower = node_name.lower()
                        
                        # Detect node type from name
                        if "kali" in node_name_lower:
                            tags.extend(["kali", "linux", "vm", "pentesting"])
                        elif "ubuntu" in node_name_lower or "linux" in node_name_lower:
                            tags.extend(["linux", "vm"])
                        elif "mac" in node_name_lower or "darwin" in node_name_lower:
                            tags.extend(["mac", "macos", "local"])
                        elif "windows" in node_name_lower:
                            tags.extend(["windows", "vm"])
                        
                        # Detect from IP patterns
                        if node_ip.startswith("192.168.64."):  # UTM default network
                            if "vm" not in tags:
                                tags.append("vm")
                            # If not yet typed and on UTM network, assume Kali
                            if len(tags) == 3:  # Only has dynamic, paired, vm
                                tags.extend(["kali", "linux"])
                        elif node_ip.startswith("192.168."):
                            if "vm" not in tags:
                                tags.append("vm")
                        
                        new_node = NodeDefinition(
                            node_id=node_id,
                            transport="http",
                            base_url=f"http://{node_ip}:8765",
                            display_name=node_name,
                            tags=tags,
                            priority=10
                        )
                        
                        # Add to registry (in-memory)
                        service.registry.add_node(new_node)
                        
                        # Try to verify connection
                        try:
                            import requests
                            health_check = requests.get(f"http://{node_ip}:8765/healthz", timeout=5)
                            is_healthy = health_check.status_code == 200
                        except:
                            is_healthy = False
                        
                        status = "✅ Online" if is_healthy else "⚠️ Offline (Unable to connect)"
                        
                        return {
                            "response": f"""🔗 **Node Connected!**
✅ **{node_name}** has been registered successfully!

**Node Details:**
• Node ID: `{node_id}`
• IP Address: `{node_ip}`
• Pairing Code: `{pairing_code}`
• Status: {status}

You can now switch to this node: `switch to {node_name}`""",
                            "context": context
                        }
                    except Exception as e:
                        return {
                            "response": f"❌ Failed to register node: {str(e)}",
                            "context": context
                        }
                else:
                    return {
                        "response": """To connect a node, use this format:

`connect to <6-digit-code> at <ip-address> and name it as <name>`

**Example:**
```
connect to 473293 at 192.168.1.50 and name it as vasanth-laptop
```

**Steps:**
1. On the remote node, run: `nacc-node init`
2. Copy the 6-digit code shown
3. Use the command above with that code""",
                        "context": context
                    }
            
            
            # ===== COMMAND EXECUTION =====
            
            # Execute any shell command - AI-powered with fallback
            if tool_name == "execute_command" or query_lower.startswith(("execute ", "run ", "exec ")):
                import re
                # Extract command after keyword
                match = re.search(r'(?:execute|run|exec)\s+(.+)', payload.query, re.IGNORECASE)
                if match:
                    command_str = match.group(1).strip()
                    
                    # Determine target node
                    target_node = context["current_node"]
                    preferred_tags = []
                    if target_node == "macbook-local":
                        preferred_tags = ["mac", "local"]
                    else:
                        preferred_tags = ["kali", "vm"]
                    
                    exec_result = service.execute_command(
                        description=f"Execute: {command_str}",
                        command=command_str.split(),
                        preferred_tags=preferred_tags,
                        timeout=payload.timeout
                    )
                    
                    results = exec_result.get('results', [{}])
                    if results:
                        stdout = results[0].get('stdout', '')
                        stderr = results[0].get('stderr', '')
                        exit_code = results[0].get('exit_code', -1)
                        
                        response = f"⚡ **Executed on {target_node}:**\n\n"
                        response += f"```\n$ {command_str}\n"
                        if stdout:
                            response += stdout
                        if stderr:
                            response += f"\n[stderr]\n{stderr}"
                        response += f"\n```\n\nExit code: {exit_code}"
                        
                        return {
                            "response": response,
                            "context": context,
                            "execution": exec_result
                        }
            
            # ===== DIRECTORY NAVIGATION =====
            
            query_lower = payload.query.lower()
            
            # Handle CD / go to directory commands - AI-powered with fallback
            if tool_name == "change_directory" or any(word in query_lower for word in ["cd ", "go to ", "navigate to", "change directory", "documents folder", "downloads folder"]):
                import re
                
                current_node = context["current_node"]
                
                # Try to extract path from query FIRST (prioritize explicit path)
                target_dir = None
                # Use original query for regex to preserve case
                path_match = re.search(r'(?:cd|go to|navigate to)\s+([\w/~.-]+)', payload.query, re.IGNORECASE)
                if path_match:
                    target_dir = path_match.group(1)
                    # Handle relative paths
                    if not target_dir.startswith('/') and not target_dir.startswith('~'):
                        import os
                        # Clean up path (remove trailing slash)
                        current = context["current_path"].rstrip('/')
                        target_dir = f"{current}/{target_dir}"
                
                # If no explicit path found, check common directory names
                if not target_dir:
                    if "documents" in query_lower:
                        target_dir = "~/Documents"
                    elif "downloads" in query_lower:
                        target_dir = "~/Downloads"
                    elif "desktop" in query_lower and current_node == "macbook-local": # Desktop is more common on Mac
                        target_dir = "~/Desktop"
                    elif "home" in query_lower:
                        target_dir = "~"
                    elif "projects" in query_lower and current_node == "macbook-local":
                        target_dir = "~/Documents/Projects"
                    elif "nacc" in query_lower and current_node != "macbook-local":
                        target_dir = "~/nacc"
                
                if target_dir:
                    # Determine preferred tags based on current node
                    try:
                        node_def = service.registry.get_definition(current_node)
                        preferred_tags = node_def.tags
                    except KeyError:
                        preferred_tags = []
                    node_label = current_node
                    
                    # Execute ls in the target directory with shell expansion
                    exec_result = service.execute_command(
                        description=f"List files in {target_dir}",
                        command=["/bin/sh", "-c", f"ls -lah {target_dir}"],
                        preferred_tags=preferred_tags,
                        timeout=payload.timeout
                    )
                    
                    stdout = exec_result.get('results', [{}])[0].get('stdout', '')
                    response_text = f"📂 **Navigated to {target_dir}** (on {node_label})\n\n```\n{stdout}\n```"
                    
                    # Update context with new path
                    context["current_path"] = target_dir
                    
                    return {
                        "response": response_text,
                        "ai_reasoning": ai_response[:200] if ai_response else "",
                        "context": context,
                        "execution": exec_result
                    }
                else:
                    return {"response": "❌ Could not determine target directory."}
            
            # List files in current or specified directory - AI-powered with fallback
            elif tool_name == "list_files" or any(word in query_lower for word in ["list", "ls", "show files", "files"]):
                path = payload.current_path or context["current_path"]
                current_node = context["current_node"]
                try:
                    node_def = service.registry.get_definition(current_node)
                    preferred_tags = node_def.tags
                except KeyError:
                    preferred_tags = []
                
                exec_result = service.execute_command(
                    description=f"List files in {path}",
                    command=["/bin/sh", "-c", f"ls -lah {path}"],
                    preferred_tags=preferred_tags,
                    timeout=payload.timeout
                )
                
                stdout = exec_result.get('results', [{}])[0].get('stdout', '')
                node_label = "MacBook Pro" if current_node == "macbook-local" else "Kali VM"
                response_text = f"📂 **Files in {path}** (on {node_label})\n\n```\n{stdout}\n```"
                
                return {
                    "response": response_text,
                    "ai_reasoning": ai_response[:200] if ai_response else "",
                    "context": context,
                    "execution": exec_result
                }
                
            # ===== FILE OPERATIONS =====
            
            # Create/Write file - AI-powered with fallback
            # Relaxed condition: "write" is enough if filename is present
            elif tool_name == "write_file" or (any(word in query_lower for word in ["create", "make", "write"]) and ("file" in query_lower or ".txt" in query_lower or ".py" in query_lower or " to " in query_lower)):
                import re
                current_node = context["current_node"]
                current_path = context["current_path"]
                try:
                    node_def = service.registry.get_definition(current_node)
                    preferred_tags = node_def.tags
                except KeyError:
                    preferred_tags = []
                node_label = current_node
                
                # Try to get filename and content from AI (support both naming conventions)
                filename = parameters.get("filename") or parameters.get("file_name") if parameters else None
                content = parameters.get("content", "") if parameters else None
                
                # Fallback to regex if AI didn't provide parameters or use extract helper
                if not filename or not content:
                    extracted_name, extracted_content = extract_filename_and_content(payload.query)
                    filename = filename or extracted_name
                    content = content or extracted_content or ""
                
                # Legacy regex fallback (kept for compatibility)
                if not filename:
                    # Extract filename and content
                    # Patterns: "create file hello.txt with content hello world"
                    #           "make a text file named hello.txt with contents hello from nacc"  
                    filename_match = re.search(r'(?:named|called)\s+([^\s]+)', payload.query, re.IGNORECASE)
                    if not filename_match:
                        # Try: "create file hello.txt"
                        filename_match = re.search(r'(?:file|txt)\s+([a-zA-Z0-9_.-]+\.\w+)', payload.query, re.IGNORECASE)
                    content_match = re.search(r'(?:with\s+)?(?:content|contents?)[\s:]+(.+)', payload.query, re.IGNORECASE)
                    
                    if filename_match:
                        filename = filename_match.group(1).strip()
                    if content_match:
                        content = content_match.group(1).strip()
                
                if filename:
                    # Build full path
                    if not filename.startswith('/'):
                        file_path = f"{current_path}/{filename}"
                    else:
                        file_path = filename
                    
                    # Try service's write_file method first
                    try:
                        write_result = service.write_file(
                            path=file_path,
                            content=content,
                            preferred_tags=preferred_tags,
                            overwrite=True
                        )
                        
                        if write_result.get('success'):
                            return {
                                "response": f"""✅ **File Created on {node_label}**

📄 **File**: `{file_path}`
📝 **Content**:
```
{content}
```

✓ File created successfully!""",
                                "context": context,
                                "execution": write_result
                            }
                    except Exception as e:
                        # FALLBACK: Use Python for restricted nodes (like Kali)
                        if "403" in str(e) or "Forbidden" in str(e):
                            # Escape content for Python string
                            content_escaped = content.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
                            python_code = f"with open('{file_path}', 'w') as f: f.write('{content_escaped}')"
                            
                            fallback_result = service.execute_command(
                                description=f"Create file {filename} via Python",
                                command=["python3", "-c", python_code],
                                preferred_tags=preferred_tags,
                                timeout=payload.timeout
                            )
                            
                            results = fallback_result.get('results', [{}])
                            if results and results[0].get('exit_code') == 0:
                                return {
                                    "response": f"""✅ **File Created on {node_label}** (via Python)

📄 **File**: `{file_path}`
📝 **Content**:
```
{content}
```

✓ File created successfully!""",
                                    "context": context,
                                    "execution": fallback_result
                                }
                            else:
                                stderr = results[0].get('stderr', '') if results else ''
                                return {
                                    "response": f"❌ Failed to create file: {stderr or 'Unknown error'}",
                                    "context": context
                                }
                        else:
                            return {
                                "response": f"❌ Failed to create file: {str(e)}",
                                "context": context
                            }
                else:
                    return {
                        "response": "❌ Could not parse filename. Please use format: `create file hello.txt with content hello world`",
                        "context": context
                    }
            
            # Read file - AI-powered with fallback
            elif tool_name == "read_file" or (any(word in query_lower for word in ["read", "show", "cat", "view", "display"]) and ("file" in query_lower or ".txt" in query_lower or "content" in query_lower)):
                import re
                current_node = context["current_node"]
                
                # Dynamic tag selection
                try:
                    node_def = service.registry.get_definition(current_node)
                    preferred_tags = node_def.tags
                except KeyError:
                    preferred_tags = []
                node_label = current_node
                
                # Try to get filename from AI parameters
                filename = parameters.get("file_name") or parameters.get("filename") if parameters else None
                
                # Fallback to regex extraction
                if not filename:
                    path_match = re.search(r'(?:read|show|cat|view|display)\s+(?:file\s+|contents?\s+of\s+)?(.+)', payload.query, re.IGNORECASE)
                    if path_match:
                        filename = path_match.group(1).strip()
                
                if filename:
                    # Build full path if needed (simple logic)
                    if not filename.startswith('/') and not filename.startswith('~'):
                        if context['current_path'] == "~":
                             file_path = filename
                        elif context['current_path'].endswith('/'):
                             file_path = f"{context['current_path']}{filename}"
                        else:
                             file_path = f"{context['current_path']}/{filename}"
                    else:
                        file_path = filename
                        
                    exec_result = service.execute_command(
                        description=f"Read file {filename}",
                        command=["/bin/sh", "-c", f"cat {file_path}"],
                        preferred_tags=preferred_tags,
                        timeout=payload.timeout
                    )
                    
                    stdout = exec_result.get('results', [{}])[0].get('stdout', '')
                    stderr = exec_result.get('results', [{}])[0].get('stderr', '')
                    
                    if stderr:
                         return {
                            "response": f"❌ Failed to read file: {stderr}",
                            "context": context
                        }
                        
                    return {
                        "response": f"📄 **File: {file_path}** (on {node_label})\n\n```\n{stdout}\n```",
                        "context": context,
                        "execution": exec_result
                    }
                else:
                     return {
                        "response": "❌ Could not determine filename to read. Please specify: `read file test.txt`",
                        "context": context
                    }

            # Delete file - AI-powered with fallback
            elif tool_name == "delete_file" or (any(word in query_lower for word in ["delete", "remove", "rm"]) and ("file" in query_lower or ".txt" in query_lower)):
                import re
                current_node = context["current_node"]
                
                # Dynamic tag selection based on current node
                # We fetch the node definition to get its tags
                try:
                    node_def = service.registry.get_definition(current_node)
                    preferred_tags = node_def.tags
                except KeyError:
                    preferred_tags = []
                node_label = current_node
                
                # Try to get filename from AI parameters
                filename = parameters.get("file_name") or parameters.get("filename") if parameters else None
                
                # Fallback to regex extraction
                if not filename:
                    path_match = re.search(r'(?:delete|remove|rm)\s+(?:file\s+)?(.+)', payload.query, re.IGNORECASE)
                    if path_match:
                        filename = path_match.group(1).strip()
                
                if filename:
                     # Build full path if needed
                    if not filename.startswith('/') and not filename.startswith('~'):
                        if context['current_path'] == "~":
                             file_path = filename
                        elif context['current_path'].endswith('/'):
                             file_path = f"{context['current_path']}{filename}"
                        else:
                             file_path = f"{context['current_path']}/{filename}"
                    else:
                        file_path = filename
                        
                    exec_result = service.execute_command(
                        description=f"Delete file {filename}",
                        command=["/bin/sh", "-c", f"rm {file_path}"],
                        preferred_tags=preferred_tags,
                        timeout=payload.timeout
                    )
                    
                    results = exec_result.get('results', [{}])
                    if results and results[0].get('exit_code') == 0:
                        return {
                            "response": f"✅ **File Deleted:** `{file_path}`",
                            "context": context,
                            "execution": exec_result
                        }
                    else:
                        stderr = results[0].get('stderr', 'Unknown error') if results else 'Unknown error'
                        return {
                            "response": f"❌ Failed to delete file: {stderr}",
                            "context": context
                        }
                else:
                    return {
                        "response": "❌ Could not determine filename to delete. Please specify: `delete file test.txt`",
                        "context": context
                    }

            # Sync/Share files - AI-powered with fallback
            elif tool_name == "sync_files" or (any(word in query_lower for word in ["share", "sync", "copy", "transfer"]) and (" to " in query_lower or " from " in query_lower)):
                import re
                
                # Try to get parameters from AI
                source_path = parameters.get("source_path") if parameters else None
                target_nodes = parameters.get("target_nodes") if parameters else None
                
                # Fallback to regex extraction
                if not source_path:
                    # Pattern: "share test.txt from kali to mac"
                    match = re.search(r'(?:share|sync|copy)\s+(.+?)\s+(?:from|to)\s+', payload.query, re.IGNORECASE)
                    if match:
                        source_path = match.group(1).strip()
                
                # Determine source and target nodes from query if not provided
                source_node = context["current_node"] # Default source
                
                # Dynamic source node detection
                available_nodes = service.list_nodes()
                for node in available_nodes:
                    node_id = node.get('node_id')
                    if node_id and f"from {node_id}" in query_lower:
                        source_node = node_id
                        break
                    
                target_node_list = []
                if target_nodes:
                    if isinstance(target_nodes, str):
                        target_node_list = [target_nodes]
                    else:
                        target_node_list = target_nodes
                else:
                    # Dynamic target node detection
                    for node in available_nodes:
                        node_id = node.get('node_id')
                        if node_id and f"to {node_id}" in query_lower:
                            target_node_list.append(node_id)
                    
                    # Fallback for common aliases
                    if not target_node_list:
                        if "to mac" in query_lower or "to local" in query_lower:
                            # Find mac node dynamically
                            for node in available_nodes:
                                if "mac" in node.get('tags', []):
                                    target_node_list.append(node.get('node_id'))
                                    break
                        elif "to kali" in query_lower or "to vm" in query_lower:
                             # Find kali node dynamically
                            for node in available_nodes:
                                if "kali" in node.get('tags', []):
                                    target_node_list.append(node.get('node_id'))
                                    break
                
                if source_path and target_node_list:
                    # Execute sync
                    sync_result = service.sync_path(
                        source_node=source_node,
                        source_path=source_path,
                        target_nodes=target_node_list
                    )
                    
                    return {
                        "response": f"✅ **Sync Initiated**\n\nSource: `{source_path}` ({source_node})\nTargets: {', '.join(target_node_list)}\n\nResult: {json.dumps(sync_result.get('targets', []), indent=2)}",
                        "context": context,
                        "execution": sync_result
                    }
                else:
                     return {
                        "response": "❌ Could not determine sync parameters. Please specify: `share file.txt from kali-vm to macbook-local`",
                        "context": context
                    }
            
            # Install packages - AI-powered with fallback
            elif tool_name == "install_package" or any(word in query_lower for word in ["install package", "install ", "apt install", "brew install", "pip install"]):
                import re
                current_node = context["current_node"]
                
                # Determine package manager and extract package name
                if "pip install" in query_lower:
                    match = re.search(r'pip install\s+(\S+)', query_lower)
                    if match:
                        package = match.group(1)
                        cmd = ["pip3", "install", package]
                elif "apt install" in query_lower or (current_node == "kali-vm" and "install" in query_lower):
                    # Handle "install X package" or "install X"
                    match = re.search(r'(?:apt\s+)?install\s+(\S+?)(?:\s+package)?', query_lower)
                    if match:
                        package = match.group(1)
                        cmd = ["sudo", "apt", "install", "-y", package]
                elif "brew install" in query_lower or (current_node == "macbook-local" and "install" in query_lower):
                    # Handle "install X package" or "install X"
                    match = re.search(r'(?:brew\s+)?install\s+(\S+?)(?:\s+package)?', query_lower)
                    if match:
                        package = match.group(1)
                        cmd = ["brew", "install", package]
                else:
                    return {
                        "response": "❌ Could not determine package manager. Please specify: `pip install`, `apt install`, or `brew install`",
                        "context": context
                    }
                
                preferred_tags = ["mac", "local"] if current_node == "macbook-local" else ["kali", "vm"]
                exec_result = service.execute_command(
                    description=f"Install package: {package}",
                    command=cmd,
                    preferred_tags=preferred_tags,
                    timeout=120  # Longer timeout for installs
                )
                
                stdout = exec_result.get('results', [{}])[0].get('stdout', '')
                stderr = exec_result.get('results', [{}])[0].get('stderr', '')
                node_label = "MacBook Pro" if current_node == "macbook-local" else "Kali VM"
                
                return {
                    "response": f"📦 **Installing {package}** on {node_label}...\n\n```\n{stdout}\n{stderr}\n```",
                    "context": context,
                    "execution": exec_result
                }
            

            
            elif tool_name == "get_status" or any(word in query_lower for word in ["status", "health", "nodes", "dashboard"]):
                # Get nodes status
                nodes = service.list_nodes()
                response_text = "🌐 **Network Status:**\n\n"
                for node in nodes:
                    node_id = node.get('node_id', 'Unknown')
                    healthy = node.get('healthy', False)
                    metrics = node.get('metrics', {})
                    
                    status = "✅ Online" if healthy else "⚠️ Offline"
                    current = "← CURRENT" if node_id == context["current_node"] else ""
                    response_text += f"• **{node_id}**: {status} {current}\n"
                    
                    if healthy and metrics:
                        cpu = metrics.get('cpu_percent', 0)
                        mem = metrics.get('memory_percent', 0)
                        disk = metrics.get('disk_percent', 0)
                        response_text += f"  CPU: {cpu:.1f}% | Memory: {mem:.1f}% | Disk: {disk:.1f}%\n"
                
                return {
                    "response": response_text,
                    "ai_reasoning": ai_response[:200] if ai_response else "",
                    "context": context
                }
                
            else:
                # Use AI reasoning if available, otherwise show help
                if reasoning and len(reasoning) > 20:
                    return {
                        "response": f"💡 {reasoning}",
                        "ai_reasoning": reasoning,
                        "context": context
                    }
                
                # Return help text
                help_text = """I can help you with:

**Node Management:**
• `switch to mac` - Switch to macOS node
• `switch to kali` - Switch to Kali VM
• `list nodes` - Show all available nodes

**Navigation:**
• `cd /path` or `go to documents` - Change directory
• `ls` or `list files` - List files in current directory

**Command Execution:**
• `execute <command>` - Run any shell command
• `read file <path>` - View file contents
• `install <package>` - Install packages (apt/brew/pip)

**System Info:**
• `status` or `dashboard` - Show node health and metrics

Currently on: **{current_node}** at `{current_path}`
""".format(current_node=context["current_node"], current_path=context["current_path"])
                
                return {
                    "response": ai_response if ai_response and len(ai_response) > 50 else help_text,
                    "ai_reasoning": ai_response[:200] if ai_response else "",
                    "context": context
                }
                
        except Exception as e:
            return {
                "response": f"❌ Error: {str(e)}",
                "context": {
                    "session_id": payload.session_id,
                    "current_node": payload.current_node,
                    "current_path": payload.current_path
                }
            }

    return app


__all__ = ["build_service", "create_app"]
