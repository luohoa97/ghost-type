import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import asyncio

app = typer.Typer(help="Manage bridges", no_args_is_help=True)
console = Console()


@app.command("doctor")
def bridge_doctor():
    """Check bridge availability."""
    console.print(Panel("[bold green]Bridge Diagnostics[/bold green]"))
    
    table = Table("Bridge", "Status", "Message")
    
    try:
        import httpx
        table.add_row("HTTP", "Available", "[green]httpx installed[/green]")
    except ImportError:
        table.add_row("HTTP", "Missing", "[red]Install httpx: uv add httpx[/red]")
    
    try:
        import websockets
        table.add_row("WebSocket", "Available", "[green]websockets installed[/green]")
    except ImportError:
        table.add_row("WebSocket", "Missing", "[red]Install websockets: uv add websockets[/red]")
    
    try:
        import mcp
        table.add_row("MCP", "Available", "[green]mcp installed[/green]")
    except ImportError:
        table.add_row("MCP", "Missing", "[red]Install mcp: uv add mcp[/red]")
    
    table.add_row("Organisely", "Optional", "Configure in config.toml")
    
    console.print(table)


@app.command("organisely-doctor")
def bridge_organisely_doctor():
    """Check Organisely bridge status."""
    console.print(Panel("[bold green]Organisely Bridge Diagnostics[/bold green]"))
    
    from ghosttype.core.config import load_config
    
    try:
        config = load_config()
    except Exception:
        console.print("[yellow]Config not found, running in demo mode[/yellow]")
        config = None
    
    table = Table("Component", "Status", "Details")
    
    try:
        from ghosttype.bridges.organisely import OrganiselyBridge
        
        bridge = OrganiselyBridge(config) if config else None
        
        diagnostics = bridge.diagnostics() if bridge else {}
        
        api_configured = diagnostics.get("api_key_configured", False)
        table.add_row(
            "API Key",
            "Configured" if api_configured else "Not Configured",
            "Set in config.toml" if api_configured else "[yellow]Add organisely_api_key to secrets[/yellow]"
        )
        
        table.add_row(
            "Status",
            diagnostics.get("status", "unknown"),
            f"URL: {diagnostics.get('base_url', 'N/A')}"
        )
        
    except ImportError:
        table.add_row("Organisely", "Missing", "[red]httpx required: uv add httpx[/red]")
    except Exception as e:
        table.add_row("Organisely", "Error", f"[red]{str(e)}[/red]")
    
    console.print(table)


@app.command("organisely-tasks")
def organisely_list_tasks(
    completed: bool = typer.Option(None, "--completed/--pending", help="Filter by completion status"),
    limit: int = typer.Option(50, "--limit", help="Maximum number of tasks"),
):
    """List tasks from Organisely."""
    console.print(Panel("[bold green]Organisely Tasks[/bold green]"))
    
    try:
        from ghosttype.core.config import load_config
        from ghosttype.bridges.organisely import OrganiselyBridge, OrganiselyConnectionStatus
        
        config = load_config()
        bridge = OrganiselyBridge(config)
        
        console.print(f"[cyan]Connecting to Organisely...[/cyan]")
        
        async def run():
            if not await bridge.connect():
                console.print("[red]Failed to connect to Organisely[/red]")
                return
            
            console.print(f"[green]Connected! Fetching tasks...[/green]")
            
            tasks = await bridge.list_tasks(completed=completed, limit=limit)
            
            if not tasks:
                console.print("[yellow]No tasks found[/yellow]")
                return
            
            table = Table("ID", "Title", "Priority", "Completed")
            for task in tasks:
                status = "[green]Yes[/green]" if task.completed else "[ ] No"
                table.add_row(task.id[:8], task.title[:40], task.priority, status)
            
            console.print(table)
            
            await bridge.disconnect()
        
        asyncio.run(run())
        
    except ImportError:
        console.print("[red]httpx library required: uv add httpx[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@app.command("organisely-create")
def organisely_create_task(
    title: str = typer.Argument(..., help="Task title"),
    priority: str = typer.Option("normal", "--priority", "-p", help="Task priority (low, normal, high, urgent)"),
    due_date: str = typer.Option(None, "--due", "-d", help="Due date (YYYY-MM-DD)"),
):
    """Create a task in Organisely."""
    console.print(Panel("[bold green]Create Organisely Task[/bold green]"))
    
    try:
        from ghosttype.core.config import load_config
        from ghosttype.bridges.organisely import OrganiselyBridge
        
        config = load_config()
        bridge = OrganiselyBridge(config)
        
        async def run():
            if not await bridge.connect():
                console.print("[red]Failed to connect to Organisely[/red]")
                return
            
            task = await bridge.create_task(
                title=title,
                priority=priority,
                due_date=due_date,
            )
            
            console.print(f"[green]Task created successfully![/green]")
            console.print(f"  ID: {task.id}")
            console.print(f"  Title: {task.title}")
            console.print(f"  Priority: {task.priority}")
            
            await bridge.disconnect()
        
        asyncio.run(run())
        
    except ImportError:
        console.print("[red]httpx library required: uv add httpx[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@app.command("http-start")
def bridge_http_start(
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to"),
    port: int = typer.Option(8765, "--port", "-p", help="Port to listen on"),
):
    """Start HTTP bridge server."""
    console.print(Panel("[bold green]Starting HTTP Bridge[/bold green]"))
    console.print(f"HTTP bridge will be available at http://{host}:{port}")
    console.print("")
    console.print("Available endpoints:")
    console.print("  GET  /health      - Health check")
    console.print("  GET  /status       - Server status")
    console.print("  POST /transcribe   - Transcribe audio")
    console.print("  POST /route        - Route text")
    console.print("  POST /execute      - Execute action")
    console.print("")
    console.print("[yellow]HTTP bridge server - use ghosttype daemon foreground for full service[/yellow]")


@app.command("websocket-start")
def bridge_websocket_start(
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to"),
    port: int = typer.Option(8766, "--port", "-p", help="Port to listen on"),
):
    """Start WebSocket bridge server."""
    console.print(Panel("[bold green]Starting WebSocket Bridge[/bold green]"))
    console.print(f"WebSocket bridge will be available at ws://{host}:{port}")
    console.print("")
    console.print("[yellow]WebSocket bridge server - use ghosttype daemon foreground for full service[/yellow]")


@app.command("mcp-start")
def bridge_mcp_start():
    """Start MCP server."""
    console.print(Panel("[bold green]Starting MCP Server[/bold green]"))
    console.print("Available MCP tools:")
    console.print("  - transcribe: Transcribe audio to text")
    console.print("  - route: Route text to appropriate action")
    console.print("  - execute: Execute an action")
    console.print("")
    console.print("[yellow]MCP server - use ghosttype daemon foreground for full service[/yellow]")


@app.command("list")
def bridge_list():
    """List all available bridges."""
    console.print(Panel("[bold green]Available Bridges[/bold green]"))
    
    table = Table("Bridge", "Type", "Description")
    
    table.add_row("HTTP", "Server", "REST API over HTTP")
    table.add_row("WebSocket", "Server", "WebSocket API for real-time communication")
    table.add_row("MCP", "Server", "Model Context Protocol server")
    table.add_row("Organisely", "Client", "Integration with Organisely task manager")
    
    console.print(table)
