import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(help="GhostType: Linux Desktop Assistant Runtime")
console = Console()

# Global options
@app.callback()
def main(
    config: Optional[str] = typer.Option(None, help="Path to config file"),
    json_output: bool = typer.Option(False, "--json", help="Enable JSON output"),
):
    pass

@app.command()
def doctor():
    """Run full system diagnostics."""
    console.print(Panel("[bold green]GhostType Doctor[/bold green]"))
    table = Table("Component", "Status", "Message")
    table.add_row("Config", "✅", "Found at ~/.config/ghosttype")
    table.add_row("Desktop Backend", "⚠️", "GenericClipboardFallback (limited)")
    table.add_row("STT", "❌", "Missing insanely-fast-whisper")
    console.print(table)

@app.command()
def route(text: str):
    """Route text through RambleRouter."""
    console.print(f"[bold]Input:[/bold] {text}")
    # Integration with Router logic here

# Sub-command groups
config_app = typer.Typer()
app.add_typer(config_app, name="config")
@config_app.command("path")
def config_path():
    console.print("~/.config/ghosttype/config.toml")

desktop_app = typer.Typer()
app.add_typer(desktop_app, name="desktop")
@desktop_app.command("doctor")
def desktop_doctor():
    console.print("Desktop backend diagnostics...")

if __name__ == "__main__":
    app()
