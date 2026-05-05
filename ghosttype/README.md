# GhostType

Linux Desktop Assistant Runtime

GhostType is a privacy-focused voice assistant for Linux that runs entirely on your desktop. It uses speech-to-text, routing, and action execution to provide a seamless voice-driven experience.

## Features

- **Privacy First**: Run entirely locally or use optional remote services
- **Universal Desktop Support**: Works with X11, GNOME, KDE, wlroots (Sway, Hyprland)
- **Modular Architecture**: Easy to extend with new providers and backends
- **Multiple Privacy Modes**: Fast, ZDR, Private, and Paranoid modes
- **Voice Commands**: Dictation, commands, and complex routing

## Architecture

GhostType is built with a modular architecture:

- **Desktop Backends**: Adaptive backends for different desktop environments
- **STT Providers**: Multiple speech-to-text options (Groq, Whisper, etc.)
- **LLM Providers**: Multiple language model options (Groq, OpenRouter, Ollama)
- **Policy Engine**: Privacy and safety policies
- **Router**: Routes voice to appropriate actions

## Installation

### Prerequisites

- Python 3.11+
- `uv` for Python package management

### Setup

```bash
# Clone the repository
git clone https://github.com/ghosttype/ghosttype.git
cd ghosttype

# Install dependencies
uv sync

# Initialize configuration
uv run ghosttype config init
```

### Optional Dependencies

#### OCR Support
```bash
# Fedora
sudo dnf install tesseract-ocr

# Ubuntu/Debian
sudo apt install tesseract-ocr
```

#### UI Support
```bash
# Fedora
sudo dnf install python3-gobject python3-gobject-devel gir1.2-adw-1

# Ubuntu/Debian
sudo apt install python3-gi gir1.2-adw-1
```

#### Local STT
```bash
uv add 'faster-whisper[torch]'
```

## Usage

### Basic Commands

```bash
# Run full diagnostics
ghosttype doctor

# Route text through router
ghosttype route "The quick brown new line fox"

# Paste text
ghosttype paste "Hello, world!"

# Transcribe audio
ghosttype transcribe --audio file.wav

# Listen in foreground mode
ghosttype listen
```

### Configuration

```bash
# Initialize default config
ghosttype config init

# Validate config
ghosttype config validate

# Print config (with secrets redacted)
ghosttype config print

# Get a config value
ghosttype config get stt.provider

# Set a config value
ghosttype config set stt.provider groq
```

### Desktop Backend

```bash
# Show selected backend
ghosttype desktop backend

# Show backend capabilities
ghosttype desktop capabilities

# Show all backends and scores
ghosttype desktop score

# Test desktop operations
ghosttype desktop paste "Hello"
ghosttype desktop type "Hello"
ghosttype desktop screenshot
```

### Providers

```bash
# List all providers
ghosttype providers list

# Check STT providers
ghosttype providers stt

# Check LLM providers
ghosttype providers llm

# Test a specific provider
ghosttype providers test groq-whisper
```

### Privacy Modes

Configure privacy mode in `config.toml`:

```toml
[app]
mode = "fast"  # or "zdr", "private", "paranoid"
```

- **Fast**: Remote operations allowed
- **ZDR**: Zero-data-removal mode
- **Private**: No remote operations, local providers only
- **Paranoid**: No remote, no screenshot, no clipboard capture

## Desktop Backend Support

GhostType automatically detects and uses the best available desktop backend:

| Backend | Detection | Capabilities |
|---------|-----------|--------------|
| X11 | `XDG_SESSION_TYPE=x11` | Full input, clipboard, screenshot |
| GNOME Wayland | `XDG_SESSION_TYPE=wayland` + GNOME | Clipboard, limited input |
| KDE Wayland | `XDG_SESSION_TYPE=wayland` + KDE | Clipboard, limited input |
| wlroots | `SWAYSOCK` or `HYPRLAND_INSTANCE_SIGNATURE` | Clipboard, input via wtype |
| Generic | Fallback | Clipboard only |

## Provider Configuration

### STT Providers

```toml
[stt]
provider = "insanely-fast-whisper"  # or "groq", "whisper-cpp", "faster-whisper"
model = "openai/whisper-large-v3"
language = "auto"
```

### LLM Providers

```toml
[secrets]
groq_api_key = "env:GROQ_API_KEY"
openrouter_api_key = "env:OPENROUTER_API_KEY"
```

## Keyd Setup

To use the F24 key for voice activation:

```bash
# Print keyd config
ghosttype keyd print-config

# Install config (requires sudo)
sudo cp ghosttype/keyd/ghosttype.conf /etc/keyd/
sudo keyd reload
```

This maps CapsLock to F24 for voice activation.

## Systemd Service

To run GhostType as a background service:

```bash
# Install service
cp ghosttype/systemd/ghosttype.service ~/.config/systemd/user/
systemctl --user enable ghosttype
systemctl --user start ghosttype

# Check status
systemctl --user status ghosttype

# View logs
journalctl --user -u ghosttype -f
```

## Development

```bash
# Run tests
uv run pytest

# Run linter
uv run ruff check .

# Type check
uv run mypy .
```

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Uses Whisper for speech recognition
- Built with Typer and Rich for CLI
- Desktop backends use xdotool, wl-copy, and other standard tools
