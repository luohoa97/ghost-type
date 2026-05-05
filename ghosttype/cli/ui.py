import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(help="Manage UI", no_args_is_help=True)
console = Console()


@app.command()
def ui():
    """Launch the GhostType UI."""
    console.print(Panel("[bold green]GhostType UI[/bold green]"))
    
    try:
        import gi
        gi.require_version("Gtk", "4.0")
        gi.require_version("Adw", "1")
        from ghosttype.packages.ghosttype_desktop.ui.app import GhostTypeApp
        
        app = GhostTypeApp()
        app.run()
    except ImportError as e:
        console.print(f"[red]Failed to import UI dependencies: {e}[/red]")
        console.print("")
        console.print("Install UI dependencies:")
        console.print("  Fedora: sudo dnf install python3-gobject python3-gobject-devel")
        console.print("  Ubuntu: sudo apt install python3-gi gir1.2-adw-1")
        raise typer.Exit(1)


@app.command("doctor")
def ui_doctor():
    """Check UI availability."""
    console.print(Panel("[bold green]UI Diagnostics[/bold green]"))
    
    table = Table("Component", "Status", "Message")
    
    try:
        import gi
        gi.require_version("Gtk", "4.0")
        gi.require_version("Adw", "1")
        from gi.repository import Gtk, Adw
        
        table.add_row("PyGObject", "✅ Available", "GTK bindings installed")
        table.add_row("libadwaita", "✅ Available", "Adw bindings installed")
    except ImportError as e:
        table.add_row("PyGObject", "❌ Missing", str(e))
        table.add_row("libadwaita", "❌ Missing", "Install python3-gobject gir1.2-adw-1")
    
    console.print(table)
