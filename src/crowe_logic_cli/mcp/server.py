"""MCP Server implementation for exposing Crowe Logic tools."""
import json
import sys
from typing import Any, Callable
from dataclasses import dataclass, field


@dataclass
class Tool:
    """A tool that can be called by MCP clients."""
    name: str
    description: str
    handler: Callable
    input_schema: dict = field(default_factory=dict)


class MCPServer:
    """MCP Server that exposes Crowe Logic tools."""
    
    def __init__(self, name: str = "crowe-logic", version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.tools: dict[str, Tool] = {}
        self._setup_default_tools()
    
    def _setup_default_tools(self):
        """Setup default Crowe Logic tools."""
        
        self.register_tool(
            name="quantum_reason",
            description="Apply Crowe Logic 4-stage quantum-inspired reasoning",
            handler=self._quantum_reason,
            input_schema={
                "type": "object",
                "properties": {
                    "problem": {"type": "string", "description": "Problem to analyze"},
                    "domain": {"type": "string", "description": "Domain context"}
                },
                "required": ["problem"]
            }
        )
        
        self.register_tool(
            name="code_review",
            description="Review code for quality and best practices",
            handler=self._code_review,
            input_schema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code to review"},
                    "language": {"type": "string", "description": "Programming language"}
                },
                "required": ["code"]
            }
        )
        
        self.register_tool(
            name="molecular_analyze",
            description="Analyze molecular structure or data",
            handler=self._molecular_analyze,
            input_schema={
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "Molecular data"},
                    "format": {"type": "string", "description": "Data format (SMILES, PDB, etc.)"}
                },
                "required": ["data"]
            }
        )
    
    def register_tool(self, name: str, description: str, handler: Callable, 
                     input_schema: dict = None):
        """Register a new tool."""
        self.tools[name] = Tool(
            name=name,
            description=description,
            handler=handler,
            input_schema=input_schema or {}
        )
    
    def _quantum_reason(self, problem: str, domain: str = "general") -> str:
        """Quantum reasoning tool handler."""
        from ..config import load_config
        from ..providers.factory import create_provider
        
        config = load_config()
        provider = create_provider(config)
        
        prompt = f"""Apply Crowe Logic 4-stage reasoning:
Problem: {problem}
Domain: {domain}

Format response with:
1. DECOMPOSITION
2. FRAMEWORK  
3. COMPUTATION
4. VALIDATION"""
        
        result = ""
        for chunk in provider.chat_completion_stream([{"role": "user", "content": prompt}]):
            result += chunk
        return result
    
    def _code_review(self, code: str, language: str = "auto") -> str:
        """Code review tool handler."""
        from ..config import load_config
        from ..providers.factory import create_provider
        
        config = load_config()
        provider = create_provider(config)
        
        prompt = f"Review this {language} code:\n```\n{code}\n```"
        
        result = ""
        for chunk in provider.chat_completion_stream([{"role": "user", "content": prompt}]):
            result += chunk
        return result
    
    def _molecular_analyze(self, data: str, format: str = "auto") -> str:
        """Molecular analysis tool handler."""
        from ..config import load_config
        from ..providers.factory import create_provider
        
        config = load_config()
        provider = create_provider(config)
        
        prompt = f"Analyze this molecular data ({format}):\n{data}"
        
        result = ""
        for chunk in provider.chat_completion_stream([{"role": "user", "content": prompt}]):
            result += chunk
        return result
    
    def handle_request(self, request: dict) -> dict:
        """Handle an incoming JSON-RPC request."""
        method = request.get("method", "")
        params = request.get("params", {})
        req_id = request.get("id")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": False},
                    },
                    "serverInfo": {
                        "name": self.name,
                        "version": self.version
                    }
                }
            }
        
        elif method == "tools/list":
            tools = [
                {
                    "name": t.name,
                    "description": t.description,
                    "inputSchema": t.input_schema
                }
                for t in self.tools.values()
            ]
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": tools}
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name not in self.tools:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
                }
            
            try:
                result = self.tools[tool_name].handler(**arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": result}]
                    }
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32000, "message": str(e)}
                }
        
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Unknown method: {method}"}
        }
    
    def run(self):
        """Run the MCP server (stdio transport)."""
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                
                request = json.loads(line)
                response = self.handle_request(request)
                
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
                
            except json.JSONDecodeError:
                continue
            except KeyboardInterrupt:
                break
