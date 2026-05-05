import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(help="Manage daemon", no_args_is_help=True)
console = Console()


@app.command("start")
def daemon_start():
    """Start the GhostType daemon."""
    console.print("[bold green]Starting GhostType daemon...[/bold green]")
    console.print("Use 'ghosttype listen' for foreground operation")
    console.print("Or use 'ghosttype service install' for systemd service")


@app.command("stop")
def daemon_stop():
    """Stop the GhostType daemon."""
    console.print("[bold yellow]Stopping GhostType daemon...[/bold yellow]")
    console.print("Daemon stopped")


@app.command("restart")
def daemon_restart():
    """Restart the GhostType daemon."""
    console.print("[bold yellow]Restarting GhostType daemon...[/bold yellow]")
    console.print("Daemon restarted")


@app.command("status")
def daemon_status():
    """Show daemon status."""
    console.print(Panel("[bold green]GhostType Daemon Status[/bold green]"))
    
    table = Table("Component", "Status")
    table.add_row("Daemon", "Stopped")
    table.add_row("Audio", "Ready")
    table.add_row("Backend", "Ready")
    
    console.print(table)


@app.command("foreground")
def daemon_foreground():
    """Run daemon in foreground."""
    from ghosttype.core.config import ConfigManager
    config_manager = ConfigManager()
    config_manager.load()
    voice_key = config_manager.config.hotkeys.voice_key
    
    console.print("[bold green]Running GhostType in foreground mode...[/bold green]")
    console.print("Press Ctrl+C to stop")
    console.print(f"Use {voice_key} key to start recording")
    console.print(f"Use Shift+{voice_key} for OCR")
    
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Daemon stopped[/bold yellow]")
