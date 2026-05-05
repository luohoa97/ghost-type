import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import Optional
import json

from ghosttype.core.config import ConfigManager
from ghosttype.core.errors import GhostTypeError

app = typer.Typer(help="GhostType: Linux Desktop Assistant Runtime", no_args_is_help=True)
console = Console()

# Subcommand modules
from . import config, desktop, providers, context, ocr, history, daemon, service, keyd, ui, bridge, debug

app.add_typer(config.app, name="config")
app.add_typer(desktop.app, name="desktop")
app.add_typer(providers.app, name="providers")
app.add_typer(context.app, name="context")
app.add_typer(ocr.app, name="ocr")
app.add_typer(history.app, name="history")
app.add_typer(daemon.app, name="daemon")
app.add_typer(service.app, name="service")
app.add_typer(keyd.app, name="keyd")
app.add_typer(ui.app, name="ui")
app.add_typer(bridge.app, name="bridge")
app.add_typer(debug.app, name="debug")


@app.callback()
def main(
    config_path: Optional[str] = typer.Option(None, "--config", help="Path to config file"),
    profile: Optional[str] = typer.Option(None, "--profile", help="Profile name"),
    json_output: bool = typer.Option(False, "--json", help="Enable JSON output"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color output"),
):
    """GhostType CLI"""
    if no_color:
        console.no_color = True


@app.command()
def doctor():
    """Run full system diagnostics."""
    console.print(Panel("[bold green]GhostType Doctor[/bold green]"))
    
    table = Table("Component", "Status", "Message")
    
    # Check config
    try:
        config = ConfigManager()
        config.load()
        table.add_row("Config", "✅ Valid", "Loaded successfully")
    except Exception as e:
        table.add_row("Config", "❌ Error", str(e))
    
    # Check desktop backend
    try:
        from ghosttype.packages.ghosttype_desktop.desktop.registry import DesktopRegistry
        backend = DesktopRegistry.detect_best_backend()
        table.add_row("Desktop", "✅ Available", f"Using {backend.get_name()}")
    except Exception as e:
        table.add_row("Desktop", "❌ Error", str(e))
    
    # Check STT providers
    try:
        from ghosttype.providers.stt.groq_whisper import GroqWhisperProvider
        provider = GroqWhisperProvider(None)
        if provider.is_available():
            table.add_row("STT", "✅ Available", "Groq Whisper ready")
        else:
            table.add_row("STT", "⚠️ Unavailable", "Check API key or dependencies")
    except Exception as e:
        table.add_row("STT", "❌ Error", str(e))
    
    # Check LLM providers
    try:
        from ghosttype.providers.llm.groq import GroqProvider
        provider = GroqProvider(None)
        if provider.is_available():
            table.add_row("LLM", "✅ Available", "Groq ready")
        else:
            table.add_row("LLM", "⚠️ Unavailable", "Check API key or dependencies")
    except Exception as e:
        table.add_row("LLM", "❌ Error", str(e))
    
    console.print(table)


@app.command()
def route(text: str):
    """Route text through RambleRouter and print validated action JSON."""
    from ghosttype.packages.ramblerouter.router import Router
    
    router = Router("groq", "llama-3.1-8b-instant")
    result = router.route(text)
    
    if json_output:
        print(json.dumps(result, indent=2))
    else:
        console.print_json(data=result)


@app.command()
def paste(text: str):
    """Insert/copy text using selected desktop backend."""
    from ghosttype.packages.ghosttype_desktop.desktop.registry import DesktopRegistry
    
    backend = DesktopRegistry.detect_best_backend()
    
    try:
        backend.paste_text(text)
        console.print(f"[green]Pasted:[/green] {text}")
    except Exception as e:
        console.print(f"[red]Failed:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def transcribe(audio: str = typer.Option(..., "--audio", help="Audio file to transcribe")):
    """Transcribe audio only, no routing."""
    console.print(f"Transcribing: {audio}")
    console.print("STT integration not yet implemented")


@app.command("run-once")
def run_once(audio: str = typer.Option(..., "--audio", help="Audio file to process")):
    """Transcribe audio, route, execute actions."""
    console.print(f"Running once with: {audio}")
    console.print("Full integration not yet implemented")


@app.command()
def listen():
    """Start hold-to-talk daemon in foreground for debugging."""
    config_manager = ConfigManager()
    config_manager.load()
    voice_key = config_manager.config.hotkeys.voice_key
    
    console.print("[bold green]Listening...[/bold green]")
    console.print(f"Press {voice_key} to start recording")
    console.print(f"Press Shift+{voice_key} for OCR")
    console.print("Press Ctrl+C to stop")
    
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Stopped[/bold yellow]")


if __name__ == "__main__":
    app()
