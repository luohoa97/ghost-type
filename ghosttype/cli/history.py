import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(help="Manage history", no_args_is_help=True)
console = Console()


@app.command("list")
def history_list():
    """List history chunks."""
    from ghosttype.packages.ghosttype_desktop.history.chunks import ChunkHistory
    from ghosttype.core.config import ConfigManager
    
    try:
        config = ConfigManager()
        config.load()
        history = ChunkHistory(config)
        chunks = history.list_chunks()
        
        if chunks:
            table = Table("ID", "Type", "Text/Key", "Reversible")
            for chunk in chunks:
                text = chunk.text[:50] + "..." if len(chunk.text) > 50 else chunk.text
                table.add_row(
                    chunk.id[:8],
                    chunk.type,
                    text,
                    "✅" if chunk.reversible else "❌"
                )
            console.print(table)
        else:
            console.print("[yellow]No history available[/yellow]")
    except Exception as e:
        console.print(f"[red]Failed to list history: {e}[/red]")
        raise typer.Exit(1)


@app.command("last")
def history_last():
    """Show last history chunk."""
    from ghosttype.packages.ghosttype_desktop.history.chunks import ChunkHistory
    from ghosttype.core.config import ConfigManager
    
    try:
        config = ConfigManager()
        config.load()
        history = ChunkHistory(config)
        chunk = history.get_last()
        
        if chunk:
            table = Table("Field", "Value")
            table.add_row("ID", chunk.id)
            table.add_row("Type", chunk.type)
            table.add_row("Text", chunk.text)
            table.add_row("Reversible", "✅" if chunk.reversible else "❌")
            console.print(table)
        else:
            console.print("[yellow]No history available[/yellow]")
    except Exception as e:
        console.print(f"[red]Failed to get last chunk: {e}[/red]")
        raise typer.Exit(1)


@app.command("undo")
def history_undo():
    """Undo last chunk."""
    from ghosttype.packages.ghosttype_desktop.history.chunks import ChunkHistory
    from ghosttype.core.config import ConfigManager
    
    try:
        config = ConfigManager()
        config.load()
        history = ChunkHistory(config)
        success = history.undo_last()
        
        if success:
            console.print("[green]Last chunk undone[/green]")
        else:
            console.print("[yellow]Nothing to undo[/yellow]")
    except Exception as e:
        console.print(f"[red]Failed to undo: {e}[/red]")
        raise typer.Exit(1)


@app.command("clear")
def history_clear():
    """Clear history."""
    from ghosttype.packages.ghosttype_desktop.history.chunks import ChunkHistory
    from ghosttype.core.config import ConfigManager
    
    try:
        config = ConfigManager()
        config.load()
        history = ChunkHistory(config)
        history.clear()
        console.print("[green]History cleared[/green]")
    except Exception as e:
        console.print(f"[red]Failed to clear history: {e}[/red]")
        raise typer.Exit(1)


@app.command("doctor")
def history_doctor():
    """Check history availability."""
    console.print(Panel("[bold green]History Diagnostics[/bold green]"))
    
    table = Table("Component", "Status", "Message")
    
    from ghosttype.packages.ghosttype_desktop.history.chunks import ChunkHistory
    from ghosttype.core.config import ConfigManager
    
    try:
        config = ConfigManager()
        config.load()
        history = ChunkHistory(config)
        table.add_row("History", "✅ Available", "History tracking enabled")
    except Exception as e:
        table.add_row("History", "❌ Error", str(e))
    
    console.print(table)
