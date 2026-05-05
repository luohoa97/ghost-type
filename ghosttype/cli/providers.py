import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import Optional

app = typer.Typer(help="Manage providers", no_args_is_help=True)
console = Console()


@app.command("list")
def providers_list():
    """List all available providers."""
    console.print(Panel("[bold green]Provider Registry[/bold green]"))
    
    table = Table("Type", "ID", "Name", "Available")
    
    # STT providers
    from ghosttype.providers.stt.base import STTProvider
    from ghosttype.providers.stt.groq_whisper import GroqWhisperProvider
    from ghosttype.providers.stt.insanely_fast_whisper import InsanelyFastWhisperProvider
    from ghosttype.providers.stt.whisper_cpp import WhisperCppProvider
    from ghosttype.providers.stt.faster_whisper import FasterWhisperProvider
    
    stt_providers = [
        ("groq-whisper", "Groq Whisper", GroqWhisperProvider),
        ("insanely-fast-whisper", "Insanely Fast Whisper", InsanelyFastWhisperProvider),
        ("whisper-cpp", "Whisper.cpp", WhisperCppProvider),
        ("faster-whisper", "Faster Whisper", FasterWhisperProvider),
    ]
    
    for provider_id, name, cls in stt_providers:
        try:
            provider = cls(None)
            available = "✅" if provider.is_available() else "❌"
        except Exception:
            available = "❌"
        table.add_row("STT", provider_id, name, available)
    
    # LLM providers
    from ghosttype.providers.llm.base import LLMProvider
    from ghosttype.providers.llm.groq import GroqProvider
    from ghosttype.providers.llm.openrouter import OpenRouterProvider
    from ghosttype.providers.llm.ollama import OllamaProvider
    
    llm_providers = [
        ("groq", "Groq", GroqProvider),
        ("openrouter", "OpenRouter", OpenRouterProvider),
        ("ollama", "Ollama", OllamaProvider),
    ]
    
    for provider_id, name, cls in llm_providers:
        try:
            provider = cls(None)
            available = "✅" if provider.is_available() else "❌"
        except Exception:
            available = "❌"
        table.add_row("LLM", provider_id, name, available)
    
    console.print(table)


@app.command("doctor")
def providers_doctor():
    """Run full provider diagnostics."""
    console.print(Panel("[bold green]Provider Diagnostics[/bold green]"))
    
    table = Table("Provider", "Status", "Message")
    
    # Check STT providers
    from ghosttype.providers.stt.groq_whisper import GroqWhisperProvider
    from ghosttype.providers.stt.insanely_fast_whisper import InsanelyFastWhisperProvider
    
    try:
        provider = GroqWhisperProvider(None)
        if provider.is_available():
            table.add_row("Groq Whisper", "✅ Available", "Ready to use")
        else:
            table.add_row("Groq Whisper", "⚠️ Unavailable", "Missing API key or dependencies")
    except Exception as e:
        table.add_row("Groq Whisper", "❌ Error", str(e))
    
    try:
        provider = InsanelyFastWhisperProvider(None)
        if provider.is_available():
            table.add_row("Insanely Fast Whisper", "✅ Available", "Local STT ready")
        else:
            table.add_row("Insanely Fast Whisper", "⚠️ Unavailable", "Missing dependencies")
    except Exception as e:
        table.add_row("Insanely Fast Whisper", "❌ Error", str(e))
    
    console.print(table)


@app.command("stt")
def providers_stt():
    """List STT providers."""
    console.print(Panel("[bold green]STT Providers[/bold green]"))
    
    table = Table("ID", "Name", "Type", "Available")
    
    from ghosttype.providers.stt.groq_whisper import GroqWhisperProvider
    from ghosttype.providers.stt.insanely_fast_whisper import InsanelyFastWhisperProvider
    from ghosttype.providers.stt.whisper_cpp import WhisperCppProvider
    from ghosttype.providers.stt.faster_whisper import FasterWhisperProvider
    
    providers = [
        ("groq-whisper", "Groq Whisper", "remote", GroqWhisperProvider),
        ("insanely-fast-whisper", "Insanely Fast Whisper", "local", InsanelyFastWhisperProvider),
        ("whisper-cpp", "Whisper.cpp", "local", WhisperCppProvider),
        ("faster-whisper", "Faster Whisper", "local", FasterWhisperProvider),
    ]
    
    for provider_id, name, provider_type, cls in providers:
        try:
            provider = cls(None)
            available = "✅" if provider.is_available() else "❌"
        except Exception:
            available = "❌"
        table.add_row(provider_id, name, provider_type, available)
    
    console.print(table)


@app.command("llm")
def providers_llm():
    """List LLM providers."""
    console.print(Panel("[bold green]LLM Providers[/bold green]"))
    
    table = Table("ID", "Name", "Type", "Available")
    
    from ghosttype.providers.llm.groq import GroqProvider
    from ghosttype.providers.llm.openrouter import OpenRouterProvider
    from ghosttype.providers.llm.ollama import OllamaProvider
    
    providers = [
        ("groq", "Groq", "remote", GroqProvider),
        ("openrouter", "OpenRouter", "remote", OpenRouterProvider),
        ("ollama", "Ollama", "local", OllamaProvider),
    ]
    
    for provider_id, name, provider_type, cls in providers:
        try:
            provider = cls(None)
            available = "✅" if provider.is_available() else "❌"
        except Exception:
            available = "❌"
        table.add_row(provider_id, name, provider_type, available)
    
    console.print(table)


@app.command("context")
def providers_context():
    """List context providers."""
    console.print(Panel("[bold green]Context Providers[/bold green]"))
    
    table = Table("ID", "Name", "Available")
    
    from ghosttype.packages.ghosttype_desktop.context.clipboard import ClipboardContextProvider
    from ghosttype.packages.ghosttype_desktop.context.selected_text import SelectedTextContextProvider
    from ghosttype.packages.ghosttype_desktop.context.active_window import ActiveWindowContextProvider
    from ghosttype.packages.ghosttype_desktop.context.last_output import LastOutputContextProvider
    from ghosttype.packages.ghosttype_desktop.context.screenshot_ocr import ScreenshotOCRContextProvider
    from ghosttype.packages.ghosttype_desktop.context.vocabulary import VocabularyContextProvider
    
    providers = [
        ("clipboard", "Clipboard", ClipboardContextProvider),
        ("selected-text", "Selected Text", SelectedTextContextProvider),
        ("active-window", "Active Window", ActiveWindowContextProvider),
        ("last-output", "Last Output", LastOutputContextProvider),
        ("screenshot-ocr", "Screenshot OCR", ScreenshotOCRContextProvider),
        ("vocabulary", "Vocabulary", VocabularyContextProvider),
    ]
    
    for provider_id, name, cls in providers:
        try:
            provider = cls(None)
            available = "✅" if provider.is_available() else "❌"
        except Exception:
            available = "❌"
        table.add_row(provider_id, name, available)
    
    console.print(table)


@app.command("desktop")
def providers_desktop():
    """List desktop backends."""
    console.print(Panel("[bold green]Desktop Backends[/bold green]"))
    
    table = Table("Name", "Score", "Capabilities")
    
    from ghosttype.packages.ghosttype_desktop.desktop.registry import DesktopRegistry
    
    backends = DesktopRegistry.detect_all()
    
    for backend in backends:
        caps = ", ".join(backend["capabilities"]) if backend["capabilities"] else "None"
        table.add_row(
            backend["name"],
            str(backend["score"]),
            caps
        )
    
    console.print(table)


@app.command("test")
def providers_test(provider_id: str):
    """Test a specific provider."""
    console.print(f"Testing provider: {provider_id}")
    
    # Try to find and test the provider
    from ghosttype.providers.stt.groq_whisper import GroqWhisperProvider
    from ghosttype.providers.stt.insanely_fast_whisper import InsanelyFastWhisperProvider
    from ghosttype.providers.llm.groq import GroqProvider
    
    provider_map = {
        "groq-whisper": GroqWhisperProvider,
        "insanely-fast-whisper": InsanelyFastWhisperProvider,
        "groq": GroqProvider,
    }
    
    if provider_id not in provider_map:
        console.print(f"[red]Provider not found: {provider_id}[/red]")
        raise typer.Exit(1)
    
    cls = provider_map[provider_id]
    try:
        provider = cls(None)
        if provider.is_available():
            console.print(f"[green]Provider {provider_id} is available[/green]")
        else:
            console.print(f"[yellow]Provider {provider_id} is not available[/yellow]")
    except Exception as e:
        console.print(f"[red]Error testing provider: {e}[/red]")
        raise typer.Exit(1)
