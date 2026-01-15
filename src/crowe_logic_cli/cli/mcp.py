"""MCP command for Model Context Protocol operations."""
import json
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(help="Model Context Protocol (MCP) operations")
console = Console()


@app.command("serve")
def serve():
    """Start Crowe Logic as an MCP server (stdio)."""
    import sys
    from ..config import load_config
    from ..providers.factory import create_provider
    
    tools = {
        "quantum_reason": {
            "description": "Apply quantum-inspired reasoning",
            "inputSchema": {
                "type": "object",
                "properties": {"problem": {"type": "string"}},
                "required": ["problem"]
            }
        },
        "code_review": {
            "description": "Review code for quality",
            "inputSchema": {
                "type": "object", 
                "properties": {"code": {"type": "string"}},
                "required": ["code"]
            }
        }
    }
    
    def handle_request(request):
        method = request.get("method", "")
        params = request.get("params", {})
        req_id = request.get("id")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0", "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "crowe-logic", "version": "2.1.0"}
                }
            }
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0", "id": req_id,
                "result": {"tools": [
                    {"name": k, **v} for k, v in tools.items()
                ]}
            }
        elif method == "tools/call":
            name = params.get("name")
            args = params.get("arguments", {})
            
            config = load_config()
            provider = create_provider(config)
            
            if name == "quantum_reason":
                prompt = f"Apply 4-stage reasoning:\n{args.get('problem')}"
            elif name == "code_review":
                prompt = f"Review this code:\n```\n{args.get('code')}\n```"
            else:
                return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Unknown tool"}}
            
            result = ""
            for chunk in provider.chat_completion_stream([{"role": "user", "content": prompt}]):
                result += chunk
            
            return {
                "jsonrpc": "2.0", "id": req_id,
                "result": {"content": [{"type": "text", "text": result}]}
            }
        
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Unknown method"}}
    
    console.print("[dim]MCP server started (stdio)[/dim]", err=True)
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            request = json.loads(line)
            response = handle_request(request)
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        except json.JSONDecodeError:
            continue
        except KeyboardInterrupt:
            break


@app.command("tools")
def list_tools():
    """List available MCP tools."""
    table = Table(title="MCP Tools")
    table.add_column("Tool", style="cyan")
    table.add_column("Description")
    
    table.add_row("quantum_reason", "Apply quantum-inspired reasoning")
    table.add_row("code_review", "Review code for quality")
    
    console.print(table)


@app.command("config")
def show_config():
    """Show MCP config for Claude Desktop."""
    config = {
        "mcpServers": {
            "crowe-logic": {
                "command": "crowelogic",
                "args": ["mcp", "serve"]
            }
        }
    }
    
    console.print(Panel(
        json.dumps(config, indent=2),
        title="[bold cyan]Claude Desktop MCP Config[/bold cyan]",
        subtitle="Add to ~/Library/Application Support/Claude/claude_desktop_config.json"
    ))
