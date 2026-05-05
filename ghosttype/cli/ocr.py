import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(help="Manage OCR operations", no_args_is_help=True)
console = Console()


@app.command("capture")
def ocr_capture():
    """Capture screen and run OCR."""
    from ghosttype.packages.ghosttype_desktop.context.screenshot_ocr import ScreenshotOCRContextProvider
    from ghosttype.core.config import ConfigManager
    
    try:
        config = ConfigManager()
        config.load()
        provider = ScreenshotOCRContextProvider(config)
        text = provider.get()
        
        if text:
            console.print(Panel(text, title="[bold green]OCR Result[/bold green]"))
        else:
            console.print("[yellow]No text detected or OCR unavailable[/yellow]")
    except Exception as e:
        console.print(f"[red]OCR failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("show")
def ocr_show():
    """Show cached OCR result."""
    from ghosttype.packages.ghosttype_desktop.context.screenshot_ocr import ScreenshotOCRContextProvider
    from ghosttype.core.config import ConfigManager
    
    try:
        config = ConfigManager()
        config.load()
        provider = ScreenshotOCRContextProvider(config)
        text = provider.get_from_cache()
        
        if text:
            console.print(Panel(text, title="[bold green]Cached OCR Result[/bold green]"))
        else:
            console.print("[yellow]No cached OCR result available[/yellow]")
    except Exception as e:
        console.print(f"[red]Failed to show cached OCR: {e}[/red]")
        raise typer.Exit(1)


@app.command("clear")
def ocr_clear():
    """Clear OCR cache."""
    from ghosttype.packages.ghosttype_desktop.context.screenshot_ocr import ScreenshotOCRContextProvider
    from ghosttype.core.config import ConfigManager
    
    try:
        config = ConfigManager()
        config.load()
        provider = ScreenshotOCRContextProvider(config)
        provider.clear_cache()
        console.print("[green]OCR cache cleared[/green]")
    except Exception as e:
        console.print(f"[red]Failed to clear OCR cache: {e}[/red]")
        raise typer.Exit(1)


@app.command("doctor")
def ocr_doctor():
    """Check OCR availability."""
    console.print(Panel("[bold green]OCR Diagnostics[/bold green]"))
    
    table = Table("Component", "Status", "Message")
    
    # Check tesseract
    import shutil
    if shutil.which("tesseract"):
        table.add_row("Tesseract", "✅ Available", "OCR engine ready")
    else:
        table.add_row("Tesseract", "❌ Missing", "Install tesseract-ocr for OCR support")
    
    # Check screenshot capability
    from ghosttype.packages.ghosttype_desktop.desktop.registry import DesktopRegistry
    capabilities = DesktopRegistry.get_capabilities()
    if any(c.value == "screenshot" for c in capabilities):
        table.add_row("Screenshot", "✅ Available", "Can capture screen")
    else:
        table.add_row("Screenshot", "❌ Unavailable", "No screenshot capability")
    
    console.print(table)
