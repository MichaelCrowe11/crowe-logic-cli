"""MCP Client implementation."""
import json
from typing import Any, Optional
from dataclasses import dataclass, field


@dataclass
class MCPTool:
    """Represents an MCP tool."""
    name: str
    description: str
    input_schema: dict = field(default_factory=dict)


@dataclass
class MCPResource:
    """Represents an MCP resource."""
    uri: str
    name: str
    mime_type: str = "text/plain"
    description: str = ""


class MCPClient:
    """Client for connecting to MCP servers."""
    
    def __init__(self, server_command: list[str], env: Optional[dict] = None):
        self.server_command = server_command
        self.env = env or {}
        self.process = None
        self.tools: list[MCPTool] = []
        self.resources: list[MCPResource] = []
        self._initialized = False
    
    async def connect(self) -> bool:
        """Connect to the MCP server."""
        import asyncio
        import subprocess
        
        try:
            self.process = await asyncio.create_subprocess_exec(
                *self.server_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**dict(__import__('os').environ), **self.env}
            )
            
            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "resources": {}
                    },
                    "clientInfo": {
                        "name": "crowe-logic-cli",
                        "version": "1.0.0"
                    }
                }
            }
            
            await self._send(init_request)
            response = await self._receive()
            
            if response and "result" in response:
                self._initialized = True
                await self._list_tools()
                await self._list_resources()
                return True
            
            return False
            
        except Exception as e:
            print(f"Failed to connect to MCP server: {e}")
            return False
    
    async def _send(self, message: dict):
        """Send a JSON-RPC message to the server."""
        if self.process and self.process.stdin:
            data = json.dumps(message) + "\n"
            self.process.stdin.write(data.encode())
            await self.process.stdin.drain()
    
    async def _receive(self) -> Optional[dict]:
        """Receive a JSON-RPC message from the server."""
        if self.process and self.process.stdout:
            line = await self.process.stdout.readline()
            if line:
                return json.loads(line.decode())
        return None
    
    async def _list_tools(self):
        """List available tools from the server."""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        await self._send(request)
        response = await self._receive()
        
        if response and "result" in response:
            for tool in response["result"].get("tools", []):
                self.tools.append(MCPTool(
                    name=tool["name"],
                    description=tool.get("description", ""),
                    input_schema=tool.get("inputSchema", {})
                ))
    
    async def _list_resources(self):
        """List available resources from the server."""
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "resources/list",
            "params": {}
        }
        await self._send(request)
        response = await self._receive()
        
        if response and "result" in response:
            for resource in response["result"].get("resources", []):
                self.resources.append(MCPResource(
                    uri=resource["uri"],
                    name=resource["name"],
                    mime_type=resource.get("mimeType", "text/plain"),
                    description=resource.get("description", "")
                ))
    
    async def call_tool(self, name: str, arguments: dict) -> Any:
        """Call a tool on the MCP server."""
        request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments
            }
        }
        await self._send(request)
        response = await self._receive()
        
        if response and "result" in response:
            return response["result"]
        elif response and "error" in response:
            raise Exception(response["error"].get("message", "Unknown error"))
        return None
    
    async def read_resource(self, uri: str) -> Optional[str]:
        """Read a resource from the MCP server."""
        request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "resources/read",
            "params": {"uri": uri}
        }
        await self._send(request)
        response = await self._receive()
        
        if response and "result" in response:
            contents = response["result"].get("contents", [])
            if contents:
                return contents[0].get("text", "")
        return None
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self.process = None
            self._initialized = False
