# Crowe Logic CLI

[![PyPI version](https://badge.fury.io/py/crowe-logic-cli.svg)](https://pypi.org/project/crowe-logic-cli/)
[![Python](https://img.shields.io/pypi/pyversions/crowe-logic-cli.svg)](https://pypi.org/project/crowe-logic-cli/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Tests](https://github.com/michaelcrowe/crowe-logic-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/michaelcrowe/crowe-logic-cli/actions/workflows/ci.yml)

A powerful, multi-provider AI CLI with quantum-enhanced scientific reasoning capabilities. Connect to Azure Claude, Azure OpenAI, or any OpenAI-compatible endpoint.

## Features

- **Multi-Provider Support**: Azure Claude (Anthropic), Azure OpenAI, OpenAI-compatible APIs
- **Streaming Responses**: Real-time output with token tracking
- **Cost Tracking**: Monitor usage and costs across sessions
- **Retry Logic**: Automatic exponential backoff on failures
- **Output Formats**: Text, JSON, Markdown with clipboard support
- **Shell Completion**: Tab completion for bash, zsh, fish
- **Azure Key Vault**: Secure credential storage
- **Conversation History**: Save, load, and resume sessions
- **Plugin System**: Extensible agent architecture

## Installation

### From PyPI (recommended)

```bash
pip install crowe-logic-cli
```

### From source

```bash
git clone https://github.com/michaelcrowe/crowe-logic-cli.git
cd crowe-logic-cli
pip install -e .
```

### Enable shell completion

```bash
# For bash
crowelogic --install-completion bash

# For zsh
crowelogic --install-completion zsh

# For fish
crowelogic --install-completion fish
```

## Quick Start

### 1. Configure your provider

```bash
# Interactive setup wizard (recommended)
crowelogic config run

# Or set environment variables
export CROWE_PROVIDER=azure
export CROWE_AZURE_ENDPOINT=https://<your-resource>.openai.azure.com
export CROWE_AZURE_DEPLOYMENT=<deployment-name>
export CROWE_AZURE_API_KEY=<key>
```

### 2. Verify connectivity

```bash
crowelogic doctor run
```

### 3. Start chatting

```bash
# Single-shot chat
crowelogic chat run "What is quantum entanglement?"

# Interactive multi-turn session
crowelogic interactive run

# Quick questions
crowelogic ask "Explain Docker in one sentence"
```

## Commands

### Chat & Interaction

```bash
# Chat with JSON output and clipboard copy
crowelogic chat run "Explain REST APIs" --output json --copy

# Chat with retry logic (default: 3 retries)
crowelogic chat run "Complex question" --retry 5

# Interactive mode with streaming
crowelogic interactive run

# Quick ask with sub-commands
crowelogic ask explain "quantum computing"
crowelogic ask how "deploy to kubernetes"
crowelogic ask fix "error: module not found"
```

### Cost Tracking

```bash
# View usage summary
crowelogic costs summary

# View today's usage
crowelogic costs today

# View last 7 days
crowelogic costs week

# Export as JSON
crowelogic costs summary --output json

# Clear usage history
crowelogic costs clear
```

### Specialized Commands

```bash
# Quantum-enhanced reasoning (4-stage framework)
crowelogic quantum run "Analyze the implications of..."

# Code analysis
crowelogic code review -f myfile.py
crowelogic code explain -f complex_algorithm.py
crowelogic code fix -f buggy.py

# Research paper analysis
crowelogic research review -f paper.pdf

# Molecular dynamics
crowelogic molecular analyze "H2O structure"
```

### Conversation History

```bash
# List saved conversations
crowelogic history list

# Resume a session
crowelogic history resume my-conversation

# Delete a conversation
crowelogic history delete old-chat
```

### Agents & Plugins

```bash
# List available agents
crowelogic agent list

# Run an agent
crowelogic agent run code-reviewer "Review this code" -f src/main.py

# List plugins
crowelogic plugins list
```

## Configuration

### Option A: Config wizard (easiest)

```bash
crowelogic config run
```

### Option B: Config file

Create `~/.crowelogic.toml`:

```toml
provider = "azure"

[azure]
endpoint = "https://<your-resource>.openai.azure.com"
deployment = "<deployment-name>"
api_key = "<api-key>"
api_version = "2024-02-15-preview"
```

### Option C: Environment variables

```bash
export CROWE_PROVIDER=azure
export CROWE_AZURE_ENDPOINT=https://<resource>.openai.azure.com
export CROWE_AZURE_DEPLOYMENT=<deployment-name>
export CROWE_AZURE_API_KEY=<api-key>
```

### Azure Key Vault Integration

Store credentials securely:

```toml
[azure]
endpoint = "https://my-resource.openai.azure.com"
deployment = "gpt-4"
api_key = "keyvault://my-vault/my-secret-name"
```

## CLI Reference

### Chat command

```bash
crowelogic chat run [OPTIONS] PROMPT

Options:
  -s, --system TEXT   Custom system prompt
  -o, --output TEXT   Output format: text, json, markdown
  -c, --copy          Copy response to clipboard
  -r, --retry INT     Number of retries (default: 3)
  -q, --quiet         Suppress retry messages
  --help              Show help
```

### Interactive mode

```bash
crowelogic interactive run [OPTIONS]

Options:
  -s, --system TEXT   Custom system prompt
  --no-stream         Disable streaming
  --help              Show help

In-session commands:
  /clear    Clear conversation history
  /save     Save conversation to history
  /system   Show current system prompt
  /exit     Exit (shows token usage)
```

## Troubleshooting

### Run diagnostics

```bash
crowelogic doctor run
```

### Common errors

| Error | Solution |
|-------|----------|
| 401 Unauthorized | Check API key and permissions |
| 404 Not Found | Verify endpoint URL and deployment name |
| 429 Rate Limited | Wait or increase `--retry` count |
| Timeout | Check network; CLI auto-retries |

## Development

### Setup

```bash
# Clone and install
git clone https://github.com/michaelcrowe/crowe-logic-cli.git
cd crowe-logic-cli
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Testing

```bash
# Run tests
make test

# With coverage
pytest --cov

# Linting
make lint

# Format
make format
```

### Building

```bash
# Build standalone executable
make build

# Build source distribution
make dist

# Generate Homebrew formula
make formula
```

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

## Author

**Michael Benjamin Crowe**
Email: michael@crowelogic.com

---

Built with [Typer](https://typer.tiangolo.com/) and [Rich](https://rich.readthedocs.io/)
