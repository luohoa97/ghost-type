import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import os
import shutil

app = typer.Typer(help="Manage systemd service", no_args_is_help=True)
console = Console()


@app.command("install")
def service_install():
    """Install the GhostType systemd service."""
    console.print(Panel("[bold green]Installing GhostType Service[/bold green]"))
    
    # Check if we're on a systemd system
    if not shutil.which("systemctl"):
        console.print("[red]systemctl not found. This system doesn't use systemd.[/red]")
        console.print("You can run 'ghosttype daemon foreground' instead")
        raise typer.Exit(1)
    
    # Check if running as user
    user = os.environ.get("USER", "unknown")
    
    console.print(f"[green]Installing user service for user: {user}[/green]")
    console.print("")
    console.print("To install the service, run:")
    console.print("  cp ghosttype/systemd/ghosttype.service ~/.config/systemd/user/")
    console.print("  systemctl --user enable ghosttype")
    console.print("  systemctl --user start ghosttype")
    console.print("")
    console.print("Or use 'ghosttype service uninstall' to remove it")


@app.command("uninstall")
def service_uninstall():
    """Uninstall the GhostType systemd service."""
    console.print(Panel("[bold yellow]Uninstalling GhostType Service[/bold yellow]"))
    
    if not shutil.which("systemctl"):
        console.print("[red]systemctl not found.[/red]")
        raise typer.Exit(1)
    
    console.print("To uninstall the service, run:")
    console.print("  systemctl --user stop ghosttype")
    console.print("  systemctl --user disable ghosttype")
    console.print("  rm ~/.config/systemd/user/ghosttype.service")


@app.command("status")
def service_status():
    """Show service status."""
    console.print(Panel("[bold green]Service Status[/bold green]"))
    
    table = Table("Component", "Status")
    table.add_row("Service", "Not installed")
    table.add_row("Audio", "Ready")
    table.add_row("Backend", "Ready")
    
    console.print(table)


@app.command("logs")
def service_logs():
    """Show service logs."""
    console.print(Panel("[bold green]Service Logs[/bold green]"))
    console.print("To view logs, run:")
    console.print("  journalctl --user -u ghosttype -f")
