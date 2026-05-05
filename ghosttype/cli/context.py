import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(help="Manage context providers", no_args_is_help=True)
console = Console()


@app.command("collect")
def context_collect():
    """Collect all available context."""
    console.print(Panel("[bold green]Collecting Context[/bold green]"))
    
    from ghosttype.packages.ghosttype_desktop.context.manager import ContextManager
    
    try:
        manager = ContextManager(None)
        context = manager.collect_all()
        
        table = Table("Context Type", "Content")
        for ctx_type, content in context.items():
            table.add_row(ctx_type, content[:100] + "..." if len(content) > 100 else content)
        
        console.print(table)
    except Exception as e:
        console.print(f"[red]Context collection failed: {e}[/red]")
        raise typer.Exit(1)


@app.command("clipboard")
def context_clipboard():
    """Get clipboard content."""
    from ghosttype.packages.ghosttype_desktop.context.clipboard import ClipboardContextProvider
    from ghosttype.core.config import ConfigManager
    
    try:
        config = ConfigManager()
        config.load()
        provider = ClipboardContextProvider(config)
        content = provider.get()
        
        if content:
            console.print(f"[green]Clipboard content:[/green]")
            console.print(content)
        else:
            console.print("[yellow]Clipboard is empty[/yellow]")
    except Exception as e:
        console.print(f"[red]Failed to get clipboard: {e}[/red]")
        raise typer.Exit(1)


@app.command("selected")
def context_selected():
    """Get selected text."""
    from ghosttype.packages.ghosttype_desktop.context.selected_text import SelectedTextContextProvider
    from ghosttype.core.config import ConfigManager
    
    try:
        config = ConfigManager()
        config.load()
        provider = SelectedTextContextProvider(config)
        content = provider.get()
        
        if content:
            console.print(f"[green]Selected text:[/green]")
            console.print(content)
        else:
            console.print("[yellow]No selected text available[/yellow]")
    except Exception as e:
        console.print(f"[red]Failed to get selected text: {e}[/red]")
        raise typer.Exit(1)


@app.command("active-window")
def context_active_window():
    """Get active window information."""
    from ghosttype.packages.ghosttype_desktop.context.active_window import ActiveWindowContextProvider
    from ghosttype.core.config import ConfigManager
    
    try:
        config = ConfigManager()
        config.load()
        provider = ActiveWindowContextProvider(config)
        info = provider.get()
        
        if info:
            table = Table("Field", "Value")
            for key, value in info.items():
                table.add_row(key, str(value))
            console.print(table)
        else:
            console.print("[yellow]Active window info not available[/yellow]")
    except Exception as e:
        console.print(f"[red]Failed to get active window: {e}[/red]")
        raise typer.Exit(1)


@app.command("last-output")
def context_last_output():
    """Get last output from history."""
    from ghosttype.packages.ghosttype_desktop.context.last_output import LastOutputContextProvider
    from ghosttype.core.config import ConfigManager
    
    try:
        config = ConfigManager()
        config.load()
        provider = LastOutputContextProvider(config)
        content = provider.get()
        
        if content:
            console.print(f"[green]Last output:[/green]")
            console.print(content)
        else:
            console.print("[yellow]No previous output available[/yellow]")
    except Exception as e:
        console.print(f"[red]Failed to get last output: {e}[/red]")
        raise typer.Exit(1)


@app.command("vocabulary")
def context_vocabulary():
    """Get vocabulary context."""
    from ghosttype.packages.ghosttype_desktop.context.vocabulary import VocabularyContextProvider
    from ghosttype.core.config import ConfigManager
    
    try:
        config = ConfigManager()
        config.load()
        provider = VocabularyContextProvider(config)
        words = provider.get()
        
        console.print(f"[green]Vocabulary words:[/green]")
        console.print(f"Total words: {len(words)}")
        console.print(f"Sample: {', '.join(words[:10])}")
    except Exception as e:
        console.print(f"[red]Failed to get vocabulary: {e}[/red]")
        raise typer.Exit(1)


@app.command("clear")
def context_clear():
    """Clear context cache."""
    from ghosttype.packages.ghosttype_desktop.context.manager import ContextManager
    from ghosttype.core.config import ConfigManager
    
    try:
        config = ConfigManager()
        config.load()
        manager = ContextManager(config)
        manager.clear()
        console.print("[green]Context cache cleared[/green]")
    except Exception as e:
        console.print(f"[red]Failed to clear context: {e}[/red]")
        raise typer.Exit(1)
