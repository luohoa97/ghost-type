import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(help="Manage bridges", no_args_is_help=True)
console = Console()


@app.command("doctor")
def bridge_doctor():
    """Check bridge availability."""
    console.print(Panel("[bold green]Bridge Diagnostics[/bold green]"))
    
    table = Table("Bridge", "Status", "Message")
    
    # Local HTTP bridge
    try:
        import httpx
        table.add_row("HTTP", "✅ Available", "httpx installed")
    except ImportError:
        table.add_row("HTTP", "❌ Missing", "Install httpx: uv add httpx")
    
    # WebSocket bridge
    try:
        import websockets
        table.add_row("WebSocket", "✅ Available", "websockets installed")
    except ImportError:
        table.add_row("WebSocket", "❌ Missing", "Install websockets: uv add websockets")
    
    # MCP bridge
    try:
        import mcp
        table.add_row("MCP", "✅ Available", "mcp installed")
    except ImportError:
        table.add_row("MCP", "❌ Missing", "Install mcp: uv add mcp")
    
    # Organisely bridge
    table.add_row("Organisely", "⚠️ Optional", "Configure in config.toml")
    
    console.print(table)


@app.command("http-start")
def bridge_http_start():
    """Start HTTP bridge server."""
    console.print(Panel("[bold green]Starting HTTP Bridge[/bold green]"))
    console.print("HTTP bridge not yet implemented")
    console.print("This will expose GhostType API over HTTP")


@app.command("websocket-start")
def bridge_websocket_start():
    """Start WebSocket bridge server."""
    console.print(Panel("[bold green]Starting WebSocket Bridge[/bold green]"))
    console.print("WebSocket bridge not yet implemented")
    console.print("This will expose GhostType API over WebSocket")


@app.command("mcp-start")
def bridge_mcp_start():
    """Start MCP server."""
    console.print(Panel("[bold green]Starting MCP Server[/bold green]"))
    console.print("MCP server not yet implemented")
    console.print("This will expose GhostType as an MCP server")


@app.command("organisely-doctor")
def bridge_organisely_doctor():
    """Check Organisely bridge status."""
    console.print(Panel("[bold green]Organisely Bridge Diagnostics[/bold green]"))
    
    table = Table("Component", "Status", "Message")
    table.add_row("Organisely", "⚠️ Configured", "Configure API key in config.toml")
    
    console.print(table)
