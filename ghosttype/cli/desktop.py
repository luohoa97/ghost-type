import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(help="Manage desktop integration", no_args_is_help=True)
console = Console()


@app.command("doctor")
def desktop_doctor():
    """Report desktop backend diagnostics."""
    console.print(Panel("[bold green]Desktop Diagnostics[/bold green]"))
    
    from ghosttype.packages.ghosttype_desktop.desktop.registry import DesktopRegistry
    
    backends = DesktopRegistry.detect_all()
    
    table = Table("Backend", "Score", "Detected", "Capabilities")
    
    for backend in backends:
        caps = ", ".join(backend["capabilities"]) if backend["capabilities"] else "None"
        detected = "✅" if backend["detected"] else "❌"
        table.add_row(
            backend["name"],
            str(backend["score"]),
            detected,
            caps
        )
    
    console.print(table)
    
    # Show selected backend
    best = DesktopRegistry.detect_best_backend()
    console.print(f"\n[bold]Selected Backend:[/bold] {best.get_name()}")


@app.command("backend")
def desktop_backend():
    """Show selected backend."""
    from ghosttype.packages.ghosttype_desktop.desktop.registry import DesktopRegistry
    
    best = DesktopRegistry.detect_best_backend()
    console.print(f"[bold]Selected Backend:[/bold] {best.get_name()}")
    console.print(f"[bold]Capabilities:[/bold] {[c.value for c in best.capabilities()]}")


@app.command("score")
def desktop_score():
    """Show scoring table for all desktop backends."""
    from ghosttype.packages.ghosttype_desktop.desktop.registry import DesktopRegistry
    
    backends = DesktopRegistry.detect_all()
    
    table = Table("Backend", "Score", "Compatible")
    
    for backend in backends:
        compatible = "Yes" if backend["detected"] else "No"
        table.add_row(backend["name"], str(backend["score"]), compatible)
    
    console.print(table)


@app.command("capabilities")
def desktop_capabilities():
    """Show selected backend capabilities."""
    from ghosttype.packages.ghosttype_desktop.desktop.registry import DesktopRegistry
    
    best = DesktopRegistry.detect_best_backend()
    
    table = Table("Capability", "Available")
    
    for cap in best.capabilities():
        table.add_row(cap.value, "✅")
    
    console.print(table)


@app.command("tools")
def desktop_tools():
    """Show detected tools."""
    from ghosttype.packages.ghosttype_desktop.desktop.registry import DesktopRegistry
    
    backends = DesktopRegistry.detect_all()
    
    console.print(Panel("[bold green]Detected Tools[/bold green]"))
    
    for backend in backends:
        if backend["detected"]:
            console.print(f"\n[bold]{backend['name']}:[/bold]")
            console.print(f"  Score: {backend['score']}")
            console.print(f"  Capabilities: {', '.join(backend['capabilities'])}")


@app.command("paste")
def desktop_paste(text: str):
    """Paste text using selected desktop backend."""
    from ghosttype.packages.ghosttype_desktop.desktop.registry import DesktopRegistry
    
    backend = DesktopRegistry.detect_best_backend()
    
    try:
        backend.paste_text(text)
        console.print(f"[green]Pasted text:[/green] {text}")
    except Exception as e:
        console.print(f"[red]Failed to paste:[/red] {e}")
        raise typer.Exit(1)


@app.command("type")
def desktop_type(text: str):
    """Type text using selected desktop backend."""
    from ghosttype.packages.ghosttype_desktop.desktop.registry import DesktopRegistry
    
    backend = DesktopRegistry.detect_best_backend()
    
    try:
        backend.type_text(text)
        console.print(f"[green]Typed text:[/green] {text}")
    except Exception as e:
        console.print(f"[red]Failed to type:[/red] {e}")
        raise typer.Exit(1)


@app.command("screenshot")
def desktop_screenshot():
    """Take a screenshot."""
    from ghosttype.packages.ghosttype_desktop.desktop.registry import DesktopRegistry
    
    backend = DesktopRegistry.detect_best_backend()
    
    try:
        img = backend.screenshot()
        if img:
            console.print(f"[green]Screenshot captured ({len(img)} bytes)[/green]")
        else:
            console.print("[yellow]Screenshot not available[/yellow]")
    except Exception as e:
        console.print(f"[red]Failed to screenshot:[/red] {e}")
        raise typer.Exit(1)


@app.command("active-window")
def desktop_active_window():
    """Get active window info."""
    from ghosttype.packages.ghosttype_desktop.desktop.registry import DesktopRegistry
    
    backend = DesktopRegistry.detect_best_backend()
    
    try:
        info = backend.get_active_window()
        if info:
            table = Table("Field", "Value")
            for key, value in info.items():
                table.add_row(key, str(value))
            console.print(table)
        else:
            console.print("[yellow]Active window info not available[/yellow]")
    except Exception as e:
        console.print(f"[red]Failed to get active window:[/red] {e}")
        raise typer.Exit(1)


@app.command("clipboard-read")
def desktop_clipboard_read():
    """Read clipboard."""
    from ghosttype.packages.ghosttype_desktop.desktop.registry import DesktopRegistry
    
    backend = DesktopRegistry.detect_best_backend()
    
    try:
        text = backend.read_clipboard()
        if text:
            console.print(f"[green]Clipboard:[/green] {text}")
        else:
            console.print("[yellow]Clipboard is empty[/yellow]")
    except Exception as e:
        console.print(f"[red]Failed to read clipboard:[/red] {e}")
        raise typer.Exit(1)


@app.command("clipboard-write")
def desktop_clipboard_write(text: str):
    """Write to clipboard."""
    from ghosttype.packages.ghosttype_desktop.desktop.registry import DesktopRegistry
    
    backend = DesktopRegistry.detect_best_backend()
    
    try:
        backend.write_clipboard(text)
        console.print(f"[green]Wrote to clipboard:[/green] {text}")
    except Exception as e:
        console.print(f"[red]Failed to write clipboard:[/red] {e}")
        raise typer.Exit(1)
