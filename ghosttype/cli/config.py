import typer
from rich.console import Console
from .utils import get_config_manager

app = typer.Typer(help="Manage configuration", no_args_is_help=True)
console = Console()

@app.command("path")
def config_path():
    """Print resolved XDG config path."""
    mgr = get_config_manager()
    console.print(str(mgr.get_path("config")))

@app.command("init")
def config_init():
    """Create full default config."""
    mgr = get_config_manager()
    mgr.init_default()
    console.print(f"Created default config at {mgr.get_path('config')}")

@app.command("validate")
def config_validate():
    """Validate TOML schema and provider references."""
    mgr = get_config_manager()
    try:
        mgr.load()
        console.print("[green]Config is valid[/green]")
    except Exception as e:
        console.print(f"[red]Config validation failed: {e}[/red]")
        raise typer.Exit(1)

@app.command("print")
def config_print():
    """Print merged config with secrets redacted."""
    mgr = get_config_manager()
    import json
    console.print_json(data=mgr.get_redacted_config())

@app.command("get")
def config_get(key: str):
    """Get a dotted config key."""
    mgr = get_config_manager()
    console.print(mgr.get_dotted(key))

@app.command("set")
def config_set(key: str, value: str):
    """Set a dotted config key."""
    mgr = get_config_manager()
    mgr.set_dotted(key, value)
    console.print(f"Set {key} = {value}")
