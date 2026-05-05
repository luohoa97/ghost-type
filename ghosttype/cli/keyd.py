import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import os
import shutil

app = typer.Typer(help="Manage keyd configuration", no_args_is_help=True)
console = Console()


@app.command("print-config")
def keyd_print_config():
    """Print keyd configuration."""
    console.print(Panel("[bold green]GhostType keyd Configuration[/bold green]"))
    
    config = """[ids]
*

[main]
capslock = f24
"""
    console.print(config)
    console.print("")
    console.print("[yellow]This maps CapsLock to F24 for voice activation.[/yellow]")


@app.command("doctor")
def keyd_doctor():
    """Check keyd availability."""
    console.print(Panel("[bold green]keyd Diagnostics[/bold green]"))
    
    table = Table("Component", "Status", "Message")
    
    if shutil.which("keyd"):
        table.add_row("keyd", "✅ Available", "keyd daemon installed")
    else:
        table.add_row("keyd", "❌ Missing", "Install keyd: sudo apt install keyd or sudo dnf install keyd")
    
    # Check if ghosttype.conf exists
    keyd_conf = "/etc/keyd/ghosttype.conf"
    if os.path.exists(keyd_conf):
        table.add_row("Config", "✅ Installed", f"Found at {keyd_conf}")
    else:
        table.add_row("Config", "⚠️ Not installed", "Run 'ghosttype keyd install-config'")
    
    console.print(table)


@app.command("install-config")
def keyd_install_config():
    """Install keyd configuration."""
    console.print(Panel("[bold green]Installing keyd Configuration[/bold green]"))
    
    config = """[ids]
*

[main]
capslock = f24
"""
    
    keyd_conf = "/etc/keyd/ghosttype.conf"
    
    console.print(f"[green]Configuration to install:[/green]")
    console.print(config)
    console.print("")
    console.print("To install, run:")
    console.print(f"  sudo mkdir -p /etc/keyd")
    console.print(f"  sudo tee {keyd_conf} << 'EOF'")
    console.print(config)
    console.print("EOF")
    console.print("")
    console.print("  sudo keyd reload")
    console.print("")
    console.print("Or manually copy the config to /etc/keyd/ghosttype.conf")
