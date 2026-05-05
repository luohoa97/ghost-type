import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import os
import json

app = typer.Typer(help="Debug commands", no_args_is_help=True)
console = Console()


@app.command("env")
def debug_env():
    """Show environment variables."""
    console.print(Panel("[bold green]Environment Variables[/bold green]"))
    
    table = Table("Variable", "Value")
    
    env_vars = [
        "XDG_SESSION_TYPE",
        "XDG_CURRENT_DESKTOP",
        "DESKTOP_SESSION",
        "WAYLAND_DISPLAY",
        "DISPLAY",
        "SWAYSOCK",
        "HYPRLAND_INSTANCE_SIGNATURE",
        "GROQ_API_KEY",
        "OPENROUTER_API_KEY",
    ]
    
    for var in env_vars:
        value = os.environ.get(var, "(not set)")
        table.add_row(var, value)
    
    console.print(table)


@app.command("paths")
def debug_paths():
    """Show resolved paths."""
    console.print(Panel("[bold green]GhostType Paths[/bold green]"))
    
    from ghosttype.core.config import ConfigManager
    
    config = ConfigManager()
    config.load()
    
    table = Table("Path Type", "Path")
    table.add_row("Config", str(config.get_path("config")))
    table.add_row("Data", str(config.get_path("data")))
    table.add_row("Cache", str(config.get_path("cache")))
    table.add_row("State", str(config.get_path("state")))
    
    console.print(table)


@app.command("config")
def debug_config():
    """Show current config."""
    console.print(Panel("[bold green]Current Configuration[/bold green]"))
    
    from ghosttype.core.config import ConfigManager
    
    config = ConfigManager()
    config.load()
    
    console.print_json(data=config.get_redacted_config())


@app.command("eventbus")
def debug_eventbus():
    """Show event bus status."""
    console.print(Panel("[bold green]Event Bus Status[/bold green]"))
    
    table = Table("Event", "Subscribers")
    table.add_row("audio_record_start", "0")
    table.add_row("audio_record_stop", "0")
    table.add_row("transcription_complete", "0")
    table.add_row("action_execute", "0")
    
    console.print(table)


@app.command("policy")
def debug_policy(text: str):
    """Check policy for text."""
    console.print(Panel("[bold green]Policy Check[/bold green]"))
    
    from ghosttype.packages.policy.engine import PolicyEngine
    from ghosttype.core.config import ConfigManager
    
    config = ConfigManager()
    config.load()
    
    engine = PolicyEngine(config)
    result = engine.check(text)
    
    table = Table("Check", "Result")
    table.add_row("Mode", result.get("mode", "unknown"))
    table.add_row("Remote Allowed", "✅" if result.get("remote_allowed", False) else "❌")
    table.add_row("Screenshot Allowed", "✅" if result.get("screenshot_allowed", False) else "❌")
    table.add_row("Clipboard Allowed", "✅" if result.get("clipboard_allowed", False) else "❌")
    
    console.print(table)


@app.command("parse")
def debug_parse(text: str):
    """Parse text through router."""
    console.print(Panel("[bold green]Parse Result[/bold green]"))
    
    from ghosttype.packages.ramblerouter.router import Router
    
    router = Router("groq", "llama-3.1-8b-instant")
    result = router.route(text)
    
    console.print_json(data=result)
