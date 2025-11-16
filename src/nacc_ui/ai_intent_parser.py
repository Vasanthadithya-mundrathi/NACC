"""
AI-Powered Intent Parser for NACC
Uses Docker Mistral-NeMo to parse natural language into structured tool execution plans
"""

import json
import subprocess
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """Represents a single tool invocation"""
    tool_name: str
    parameters: Dict[str, Any]
    reason: str
    order: int


@dataclass
class ExecutionPlan:
    """Structured execution plan from AGENTIC AI"""
    intent: str  # navigate, create_file, execute_command, sync_files, network_scan, etc.
    tools: List[ToolCall]
    target_path: Optional[str] = None
    content: Optional[str] = None
    confidence: float = 0.7
    reasoning: str = ""
    target_node: Optional[str] = None  # Which node to execute on (kali-vm, laptop, server, etc.)
    execution_strategy: str = "sequential"  # sequential, parallel, distributed


class PathResolver:
    """Intelligent path resolution with context awareness"""
    
    COMMON_FOLDERS = {
        'downloads': 'Downloads',
        'download': 'Downloads',
        'documents': 'Documents',
        'document': 'Documents',
        'desktop': 'Desktop',
        'pictures': 'Pictures',
        'picture': 'Pictures',
        'photos': 'Pictures',
        'music': 'Music',
        'videos': 'Videos',
        'video': 'Videos',
        'home': '',  # User home directory
        'root': '/',
    }
    
    def __init__(self, current_path: str, user_home: str, os_type: str = 'linux'):
        self.current_path = Path(current_path)
        self.user_home = Path(user_home)
        self.os_type = os_type
    
    def resolve(self, path_str: str) -> str:
        """
        Intelligently resolve a path from natural language
        
        Examples:
            'downloads folder' -> '/home/user/Downloads'
            'the downloads' -> '/home/user/Downloads'
            'Documents' -> '/home/user/Documents'
            './file.txt' -> '/home/user/current/file.txt'
            'hello.txt' -> '/home/user/current/hello.txt'
        """
        # Clean the input
        path_str = path_str.strip().strip('"\'')
        path_lower = path_str.lower()
        
        # Remove common article words
        for article in ['the ', 'a ', 'an ', 'my ', 'your ']:
            if path_lower.startswith(article):
                path_lower = path_lower[len(article):]
                path_str = path_str[len(article):]
        
        # Remove 'folder' or 'directory' suffix
        for suffix in [' folder', ' directory', ' dir']:
            if path_lower.endswith(suffix):
                path_lower = path_lower[:-len(suffix)]
                path_str = path_str[:-len(suffix)]
        
        # Check if it's a common folder name
        if path_lower in self.COMMON_FOLDERS:
            folder_name = self.COMMON_FOLDERS[path_lower]
            if folder_name:
                return str(self.user_home / folder_name)
            else:
                return str(self.user_home)
        
        # Absolute path
        if path_str.startswith('/'):
            return path_str
        
        # Relative path (starts with ./)
        if path_str.startswith('./'):
            return str(self.current_path / path_str[2:])
        
        # Parent directory
        if path_str.startswith('../'):
            return str(self.current_path / path_str)
        
        # Check if it's a folder in user home
        potential_path = self.user_home / path_str
        # For now, assume it's relative to current directory if it exists
        # In a real system, you'd check if the path exists
        
        # Default: relative to current directory
        return str(self.current_path / path_str)
    
    def get_user_home(self) -> str:
        """Get the user home directory"""
        return str(self.user_home)


class AIIntentParser:
    """Uses Docker AI to parse user intent into structured execution plans"""
    
    def __init__(self, model_name: str = "mistral-nemo", timeout: float = 30.0, use_ai: bool = True, use_fallback: bool = False):
        """
        Initialize intent parser for AGENTIC NETWORK CONTROL.
        
        Args:
            model_name: Docker model name (default: mistral-nemo for accuracy)
            timeout: AI inference timeout in seconds (default: 30.0 for complex network orchestration)
            use_ai: Whether to use AI model (default: True)
            use_fallback: Whether to use fallback on AI failure (default: False - pure AI mode)
                   
        AGENTIC CAPABILITIES:
            - Multi-node orchestration (select which machine to execute on)
            - MCP tool integration (ListFiles, ReadFile, WriteFile, ExecuteCommand, SyncFiles, GetNodeInfo)
            - Remote access across network of computers
            - Parallel execution and file synchronization
            - Code generation with execution planning
        """
        self.model_name = model_name
        self.timeout = timeout
        self.use_ai = use_ai
        self.use_fallback = use_fallback  # Pure AI mode: no fallback
        self._ai_available = None  # Cache AI availability
        if use_ai:
            self._check_ai_availability()
    
    def _check_ai_availability(self):
        """Check if Docker AI is available"""
        try:
            result = subprocess.run(
                ["docker", "model", "ls"],
                capture_output=True,
                text=True,
                timeout=2
            )
            self._ai_available = result.returncode == 0 and self.model_name in result.stdout
            if self._ai_available:
                logger.info(f"Docker AI {self.model_name} is available")
            else:
                logger.warning(f"Docker AI {self.model_name} not found, using fallback only")
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"Docker not available: {e}, using fallback only")
            self._ai_available = False
    
    def parse(self, user_message: str, context: Dict[str, Any]) -> ExecutionPlan:
        """
        Parse user message into structured execution plan using AGENTIC AI
        
        Args:
            user_message: Natural language command from user
            context: Current session context (path, node, OS, available nodes, etc.)
        
        Returns:
            ExecutionPlan with tools, node selection, and execution strategy
        """
        # PURE AI MODE: Check if AI is available
        if not self.use_ai or not self._ai_available:
            if self.use_fallback:
                logger.info("AI unavailable, using fallback")
                return self._fallback_parse(user_message, context)
            else:
                raise RuntimeError("AI is required but not available. Start Docker Desktop or enable fallback mode.")
        
        # AI parsing with extended timeout for complex network orchestration
        try:
            # Build comprehensive AI prompt for network orchestration
            prompt = self._build_prompt(user_message, context)
            
            # Call Docker AI (Mistral-NeMo) - allows up to 30s for complex reasoning
            logger.info(f"🤖 Calling AI (timeout: {self.timeout}s) for: {user_message[:60]}...")
            ai_response = self._call_docker_ai(prompt)
            
            # Parse AI response into structured execution plan
            plan = self._parse_ai_response(ai_response, context)
            
            logger.info(f"✅ AI parsed intent: {plan.intent}, confidence: {plan.confidence * 100:.0f}%")
            logger.info(f"   Target node: {plan.target_node or 'auto-select'}")
            logger.info(f"   Tools: {[t.tool_name for t in plan.tools]}")
            return plan
            
        except subprocess.TimeoutExpired:
            if self.use_fallback:
                logger.warning(f"Docker AI timeout ({self.timeout}s), using fallback")
                return self._fallback_parse(user_message, context)
            else:
                raise RuntimeError(f"AI timeout after {self.timeout}s. The task may be too complex or Docker AI is slow.")
        except Exception as e:
            if self.use_fallback:
                logger.warning(f"AI parsing failed: {e}, using fallback")
                return self._fallback_parse(user_message, context)
            else:
                # PURE AI MODE: Fail fast, show real errors
                logger.error(f"❌ AI parsing failed: {e}")
                raise RuntimeError(f"AI parsing failed: {e}. Check Docker Desktop and model availability.")
    
    def _build_prompt(self, user_message: str, context: Dict[str, Any]) -> str:
        """Build AGENTIC prompt for multi-node network orchestration"""
        
        current_path = context.get('current_path', '/home/user')
        user_home = context.get('user_home', '/home/user')
        os_type = context.get('os_type', 'linux')
        current_node = context.get('current_node', 'local')
        available_nodes = context.get('available_nodes', [])
        
        # Build node descriptions for intelligent routing
        nodes_info = ""
        if available_nodes:
            nodes_info = "\n\nAVAILABLE NETWORK NODES:\n"
            for node in available_nodes:
                nodes_info += f"- {node.get('node_id', 'unknown')}: {node.get('tags', [])} ({node.get('os_type', 'unknown')})\n"
        
        # Comprehensive prompt for network orchestration
        prompt = f"""You are an AGENTIC AI that controls a NETWORK OF COMPUTERS through MCP (Model Context Protocol).

USER COMMAND: "{user_message}"

CONTEXT:
- Current directory: {current_path}
- User home: {user_home}
- Current node: {current_node}
- OS: {os_type}{nodes_info}

MCP TOOLS (6 CORE TOOLS):
1. list_files(path, node_id) - List files on any node
2. read_file(filepath, node_id) - Read file from any node
3. write_file(filepath, content, node_id) - Write file to any node
4. execute_command(command, node_id) - Execute shell command on any node
5. sync_files(source_node, source_path, target_node, target_path) - Sync files between nodes
6. get_node_info(node_id) - Get node capabilities, status, resources

NODE SELECTION RULES:
- Security tasks (nmap, nikto, metasploit) → kali-vm (has security tools)
- General commands → current node or any Linux node
- File operations → node where file exists
- Parallel tasks → distribute across multiple nodes
- Sync operations → specify source and target nodes

OUTPUT FORMAT (JSON):
{{
  "intent": "brief description",
  "target_node": "node_id or null for auto-select",
  "execution_strategy": "sequential|parallel|distributed",
  "target_path": "file/directory path if applicable",
  "content": "file content if creating files",
  "tools": [
    {{
      "tool_name": "exact tool name",
      "parameters": {{"param": "value", "node_id": "target"}},
      "reason": "why this tool",
      "order": 1
    }}
  ],
  "confidence": 0.95,
  "reasoning": "explain your decision"
}}

EXAMPLES:

Command: "run nmap scan on local network"
{{"intent":"network_scan","target_node":"kali-vm","execution_strategy":"sequential","tools":[{{"tool_name":"execute_command","parameters":{{"command":"nmap -sn 192.168.1.0/24","node_id":"kali-vm"}},"reason":"kali-vm has nmap","order":1}}],"confidence":0.9,"reasoning":"Security scan requires kali-vm"}}

Command: "sync my documents folder from laptop to server"
{{"intent":"sync_files","execution_strategy":"sequential","tools":[{{"tool_name":"sync_files","parameters":{{"source_node":"laptop","source_path":"/home/user/Documents","target_node":"server","target_path":"/backup/Documents"}},"reason":"cross-node sync","order":1}}],"confidence":0.95,"reasoning":"File sync between two nodes"}}

Command: "create hello.txt in downloads"
{{"intent":"create_file","target_path":"{user_home}/Downloads/hello.txt","content":"","tools":[{{"tool_name":"write_file","parameters":{{"filepath":"{user_home}/Downloads/hello.txt","content":"","node_id":"{current_node}"}},"reason":"create file","order":1}}],"confidence":0.9,"reasoning":"Simple file creation on current node"}}

Command: "execute python script on all linux nodes"
{{"intent":"parallel_execution","execution_strategy":"parallel","tools":[{{"tool_name":"execute_command","parameters":{{"command":"python3 /tmp/script.py","node_id":"ALL_LINUX"}},"reason":"run on all linux nodes","order":1}}],"confidence":0.85,"reasoning":"Parallel execution across multiple nodes"}}

Now parse the user command. Output ONLY valid JSON, no explanations:"""
        
        return prompt
    
    def _call_docker_ai(self, prompt: str) -> str:
        """Call Docker AI model for completion"""
        try:
            result = subprocess.run(
                ["docker", "model", "run", self.model_name, prompt],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Docker AI failed: {result.stderr}")
            
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Docker AI timeout")
        except FileNotFoundError:
            raise RuntimeError("Docker not found")
    
    def _parse_ai_response(self, ai_response: str, context: Dict[str, Any]) -> ExecutionPlan:
        """Parse AI's JSON response into ExecutionPlan"""
        try:
            # Extract JSON from response (in case AI adds extra text)
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in AI response")
            
            json_str = ai_response[json_start:json_end]
            parsed = json.loads(json_str)
            
            # Build ToolCall objects
            tool_calls = []
            for t in parsed.get('tools', []):
                tool_calls.append(ToolCall(
                    tool_name=t['tool_name'],
                    parameters=t['parameters'],
                    reason=t['reason'],
                    order=t['order']
                ))
            
            # Sort by order
            tool_calls.sort(key=lambda x: x.order)
            
            return ExecutionPlan(
                intent=parsed['intent'],
                tools=tool_calls,
                target_path=parsed.get('target_path'),
                content=parsed.get('content'),
                confidence=float(parsed.get('confidence', 0.7)),
                reasoning=parsed.get('reasoning', 'AI parsed successfully'),
                target_node=parsed.get('target_node'),  # NEW: Node selection
                execution_strategy=parsed.get('execution_strategy', 'sequential')  # NEW: Execution strategy
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.debug(f"AI response was: {ai_response[:200]}")
            raise
    
    def _fallback_parse(self, user_message: str, context: Dict[str, Any]) -> ExecutionPlan:
        """
        Enhanced fallback heuristic parsing when AI fails
        Production-grade parser that handles 90% of common cases
        """
        message_lower = user_message.lower()
        current_path = context.get('current_path', '/home/user')
        user_home = context.get('user_home', '/home/user')
        
        # Initialize path resolver
        resolver = PathResolver(current_path, user_home)
        
        # Detect intent
        intent = "unknown"
        tools = []
        target_path = None
        content = None
        
        # ============================================================================
        # COMPOUND INTENT: Navigate + Create File
        # Example: "navigate to downloads and make a file which says hello"
        # ============================================================================
        if ('navigate' in message_lower or 'go to' in message_lower) and \
           ('make' in message_lower or 'create' in message_lower):
            intent = "navigate_and_create"
            
            # Extract target folder
            folder_path = current_path
            for folder_name in ['downloads', 'documents', 'desktop', 'pictures', 'home']:
                if folder_name in message_lower:
                    folder_path = resolver.resolve(folder_name)
                    break
            
            # Extract filename
            filename = "newfile.txt"
            words = user_message.split()
            for word in words:
                if '.' in word:
                    filename = word.strip('.,!?')
                    break
            
            # Extract content
            content = ""
            for marker in [' says ', ' which says ', ' that says ', ' with content ', ' containing ']:
                if marker in message_lower:
                    content = user_message.split(marker, 1)[1].strip()
                    content = content.rstrip('.,!?')
                    break
            
            target_path = f"{folder_path}/{filename}"
            
            # Build tool sequence
            tools = [
                ToolCall(
                    tool_name="list_files",
                    parameters={"path": folder_path},
                    reason="Navigate to target folder",
                    order=1
                ),
                ToolCall(
                    tool_name="write_file",
                    parameters={"filepath": target_path, "content": content},
                    reason="Create file with specified content",
                    order=2
                )
            ]
        
        # ============================================================================
        # CODE GENERATION: Create script/code files
        # Example: "create python script calculator.py with add and subtract functions"
        # ============================================================================
        elif any(word in message_lower for word in ['script', 'code', 'function', 'class', 'program']):
            intent = "generate_code"
            
            # Extract filename
            words = user_message.split()
            filename = None
            for word in words:
                if '.' in word and any(ext in word.lower() for ext in ['.py', '.js', '.java', '.cpp', '.c', '.go']):
                    filename = word.strip('.,!?')
                    break
            
            if not filename:
                # Infer from language keywords
                if 'python' in message_lower or '.py' in message_lower:
                    filename = "script.py"
                elif 'javascript' in message_lower or '.js' in message_lower:
                    filename = "script.js"
                else:
                    filename = "script.txt"
            
            # Generate basic code template based on requirements
            content = ""
            if 'python' in message_lower or filename.endswith('.py'):
                if 'function' in message_lower:
                    # Extract function names
                    if 'add' in message_lower and 'subtract' in message_lower:
                        content = "def add(a, b):\n    return a + b\n\ndef subtract(a, b):\n    return a - b\n"
                    elif 'add' in message_lower:
                        content = "def add(a, b):\n    return a + b\n"
                    else:
                        content = "# Python script\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n"
                elif 'class' in message_lower:
                    content = "class MyClass:\n    def __init__(self):\n        pass\n"
                else:
                    content = "# Python script\nprint('Hello, World!')\n"
            
            target_path = f"{current_path}/{filename}"
            
            tools = [
                ToolCall(
                    tool_name="write_file",
                    parameters={"filepath": target_path, "content": content},
                    reason="Generate code file",
                    order=1
                )
            ]
        
        # ============================================================================
        # DIRECTORY CREATION: Make folders
        # Example: "create a new directory called test_project"
        # ============================================================================
        elif 'directory' in message_lower or 'folder' in message_lower:
            if any(word in message_lower for word in ['create', 'make', 'mkdir']):
                intent = "create_directory"
                
                # Extract directory name
                words = user_message.split()
                dir_name = "new_directory"
                for i, word in enumerate(words):
                    if word.lower() in ['called', 'named'] and i + 1 < len(words):
                        dir_name = words[i + 1].strip('.,!?')
                        break
                
                target_path = f"{current_path}/{dir_name}"
                
                # Check if there's also a file creation request
                if 'readme' in message_lower or 'file' in message_lower:
                    intent = "create_directory_and_file"
                    tools = [
                        ToolCall(
                            tool_name="create_directory",
                            parameters={"path": target_path},
                            reason="Create new directory",
                            order=1
                        ),
                        ToolCall(
                            tool_name="write_file",
                            parameters={"filepath": f"{target_path}/README.md", "content": f"# {dir_name}\n\nProject directory\n"},
                            reason="Create README in new directory",
                            order=2
                        )
                    ]
                else:
                    tools = [
                        ToolCall(
                            tool_name="create_directory",
                            parameters={"path": target_path},
                            reason="Create new directory",
                            order=1
                        )
                    ]
        
        # ============================================================================
        # SIMPLE INTENT: Create file only
        # ============================================================================
        elif any(word in message_lower for word in ['create', 'make', 'write', 'add']):
            if any(word in message_lower for word in ['file', 'text', 'document']):
                intent = "create_file"
                
                # Extract filename (look for common extensions)
                words = user_message.split()
                filename = None
                for word in words:
                    if '.' in word or word.lower().endswith(('.txt', '.md', '.py', '.js', '.json', '.yml')):
                        filename = word.strip('.,!?')
                        break
                
                if not filename:
                    filename = "newfile.txt"
                
                # Extract content (multiple patterns)
                content = ""
                for marker in [' says ', ' which says ', ' that says ', ' with content ', ' containing ', ' with text ']:
                    if marker in message_lower:
                        content = user_message.split(marker, 1)[1].strip()
                        content = content.rstrip('.,!?')
                        break
                
                # Resolve target folder
                folder_path = current_path
                for folder_name in ['downloads', 'documents', 'desktop', 'pictures']:
                    if folder_name in message_lower and ('in ' in message_lower or 'to ' in message_lower):
                        folder_path = resolver.resolve(folder_name)
                        break
                
                target_path = f"{folder_path}/{filename}"
                
                tools = [
                    ToolCall(
                        tool_name="write_file",
                        parameters={"filepath": target_path, "content": content},
                        reason="Create file with specified content",
                        order=1
                    )
                ]
        
        # ============================================================================
        # SIMPLE INTENT: Navigate only
        # ============================================================================
        elif any(word in message_lower for word in ['navigate', 'go to', 'open', 'cd', 'change to']):
            intent = "navigate"
            
            # Extract folder name (improved detection)
            folder_path = current_path
            for folder_name in ['downloads', 'documents', 'desktop', 'pictures', 'music', 'videos', 'home']:
                if folder_name in message_lower:
                    folder_path = resolver.resolve(folder_name)
                    break
            
            target_path = folder_path
            
            tools = [
                ToolCall(
                    tool_name="list_files",
                    parameters={"path": target_path},
                    reason="Navigate and list directory contents",
                    order=1
                )
            ]
        
        # ============================================================================
        # SIMPLE INTENT: List files
        # ============================================================================
        elif any(word in message_lower for word in ['list', 'show', 'files', 'ls', 'what files']):
            intent = "list_files"
            
            # Check if user specified a folder
            folder_path = current_path
            for folder_name in ['downloads', 'documents', 'desktop', 'pictures']:
                if folder_name in message_lower:
                    folder_path = resolver.resolve(folder_name)
                    break
            
            target_path = folder_path
            
            tools = [
                ToolCall(
                    tool_name="list_files",
                    parameters={"path": target_path},
                    reason="List directory contents",
                    order=1
                )
            ]
        
        # ============================================================================
        # Calculate confidence based on how well we matched
        # ============================================================================
        confidence = 0.5  # Base fallback confidence
        
        if tools:
            # Increase confidence if we found clear markers
            if intent == "navigate_and_create":
                confidence = 0.85  # High confidence for compound intents
            elif intent == "create_file" and content:
                confidence = 0.80  # High confidence if we extracted content
            elif intent in ["navigate", "list_files"]:
                confidence = 0.75  # Good confidence for simple navigation
        
        return ExecutionPlan(
            intent=intent,
            tools=tools,
            target_path=target_path,
            content=content,
            confidence=confidence,
            reasoning=f"Enhanced fallback parsing (AI unavailable) - Detected: {intent}"
        )


def test_parser():
    """Test the intent parser"""
    parser = AIIntentParser()
    
    test_cases = [
        {
            "message": "navigate to the downloads folder and make a text file which says hello this is nacc",
            "context": {
                "current_path": "/home/vasanth",
                "user_home": "/home/vasanth",
                "current_node": "kali-vm",
                "os_type": "linux"
            }
        }
    ]
    
    for test in test_cases:
        print(f"\nTesting: {test['message']}")
        print("=" * 80)
        
        plan = parser.parse(test['message'], test['context'])
        print(f"Intent: {plan.intent}")
        print(f"Target Path: {plan.target_path}")
        print(f"Content: {plan.content}")
        print(f"Confidence: {plan.confidence}")
        print(f"Reasoning: {plan.reasoning}")
        print(f"\nTools to execute:")
        for tool in plan.tools:
            print(f"  {tool.order}. {tool.tool_name}({tool.parameters})")
            print(f"     Reason: {tool.reason}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_parser()
