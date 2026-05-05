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
        from gi.repository import Gtk, Gdk, Adw
        from ghosttype.ghosttype_desktop.ui.app import GhostTypeApplication, main as ui_main
        
        ui_main()
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
    
    from rich.table import Table
    table = Table("Component", "Status", "Message")
    
    gtk_available = False
    adw_available = False
    
    try:
        import gi
        gi.require_version("Gtk", "4.0")
        from gi.repository import Gtk
        gtk_available = True
    except (ImportError, ValueError) as e:
        pass
    
    try:
        import gi
        gi.require_version("Adw", "1")
        from gi.repository import Adw
        adw_available = True
    except (ImportError, ValueError) as e:
        pass
    
    if gtk_available:
        table.add_row("PyGObject", "[green]Available[/green]", "GTK 4 bindings installed")
    else:
        table.add_row("PyGObject", "[red]Missing[/red]", "Install python3-gi")
    
    if adw_available:
        table.add_row("libadwaita", "[green]Available[/green]", "Adw bindings installed")
    else:
        table.add_row("libadwaita", "[red]Missing[/red]", "Install gir1.2-adw-1")
    
    if gtk_available and adw_available:
        table.add_row("UI", "[green]Ready[/green]", "Run 'ghosttype ui' to launch")
    else:
        table.add_row("UI", "[yellow]Not Ready[/yellow]", "Install dependencies above")
    
    console.print(table)
