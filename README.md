# Crowe Logic CLI

A standalone CLI you can customize (UX, commands, workflows) while connecting to your own model endpoints.

## Install (dev)

From this folder:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Quick Start

Run the interactive configuration wizard:

```bash
crowelogic config run
```

This will guide you through:
- Provider selection (Azure AI Inference, Azure OpenAI, OpenAI-compatible)
- Endpoint and credential setup
- Optional Azure Key Vault integration
- Connection testing

## Configuration

You can configure the CLI using **environment variables** or a **config file**.

### Option A: Config wizard (easiest)

```bash
crowelogic config run
```

### Option B: Config file (manual)

Copy the example and fill in your values:

```bash
cp .crowelogic.toml.example ~/.crowelogic.toml
# Edit ~/.crowelogic.toml with your endpoint details
```

The CLI searches for `.crowelogic.toml` in:
1. Current directory (and parents)
2. Home directory (`~/.crowelogic.toml`)

### Option C: Environment variables

```bash
export CROWE_PROVIDER=azure
export CROWE_AZURE_ENDPOINT=https://<your-resource>.openai.azure.com
export CROWE_AZURE_DEPLOYMENT=<deployment-name>
export CROWE_AZURE_API_KEY=<key>
export CROWE_AZURE_API_VERSION=2024-02-15-preview
```

## Commands

### Setup and diagnostics

```bash
# Interactive setup wizard
crowelogic config run

# Verify connectivity with enhanced diagnostics
crowelogic doctor run
```

### Chat

```bash
# Single-shot chat
crowelogic chat run "What is the capital of France?"

# Interactive multi-turn session with streaming and token tracking
crowelogic interactive run

# Save conversation during interactive session
# (Type /save <name> in the REPL)

# Resume a saved conversation
crowelogic history resume my-conversation
```

### Conversation history

```bash
# List saved conversations
crowelogic history list

# Load and display a conversation
crowelogic history load my-conversation

# Resume interactive session from history
crowelogic history resume my-conversation

# Delete a conversation
crowelogic history delete my-conversation
```

### Agents and plugins

```bash
# List available agents from plugins directory
crowelogic agent list

# Run an agent with a prompt
crowelogic agent run code-reviewer "Review this function"

# List plugins
crowelogic plugins list

# Show plugin details
crowelogic plugins show hookify
```

### Interactive mode commands

In `crowelogic interactive run`:
- `/clear` — Clear conversation history
- `/save <name>` — Save conversation to history
- `/system` — Show current system prompt
- `/exit` — Exit (shows session token usage)

Token tracking is automatically displayed after each response and on exit.

## For OpenAI-compatible endpoints

If your Azure endpoint uses a generic OpenAI-compatible API (not `*.openai.azure.com`):

```toml
provider = "openai_compatible"

[openai_compatible]
base_url = "https://<your-endpoint>"
model = "<model-id>"
api_key = "<your-api-key>"
```

## CLI Flags Reference

### Chat command

```bash
crowelogic chat run [OPTIONS] PROMPT

Options:
  -s, --system TEXT   Custom system prompt
  --help              Show help message
```

### Interactive command

```bash
crowelogic interactive run [OPTIONS]

Options:
  -s, --system TEXT   Custom system prompt (default: "You are a helpful assistant.")
  --no-stream         Disable streaming responses
  --help              Show help message
```

### Agent command

```bash
crowelogic agent run [OPTIONS] AGENT_NAME PROMPT

Options:
  -f, --file PATH     Include file content as context
  --no-stream         Disable streaming responses
  --help              Show help message

Examples:
  crowelogic agent run code-reviewer "Review this code" -f src/main.py
  crowelogic agent run ./my-agent.md "Help me with this task"
```

### History command

```bash
crowelogic history resume [OPTIONS] NAME

Options:
  --no-stream         Disable streaming responses
  --help              Show help message
```

### Config command

```bash
crowelogic config show      # Display current configuration
crowelogic config path      # Show config file search paths
crowelogic config init      # Create a template config file
```

## Azure Key Vault Integration

Store API keys securely using Azure Key Vault:

```toml
[azure]
endpoint = "https://my-resource.openai.azure.com"
deployment = "gpt-4"
api_key = "keyvault://my-vault/my-secret-name"
```

The CLI uses `DefaultAzureCredential` for authentication, which supports:
- Environment variables (`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET`)
- Managed Identity (when running in Azure)
- Azure CLI (`az login`)
- Visual Studio Code credentials

## Troubleshooting

### Configuration errors

**"Missing required config for Azure provider"**

Ensure all required fields are set. For Azure:
```bash
export CROWE_AZURE_ENDPOINT=https://<resource>.openai.azure.com
export CROWE_AZURE_DEPLOYMENT=<deployment-name>
export CROWE_AZURE_API_KEY=<api-key>
```

Or in `.crowelogic.toml`:
```toml
provider = "azure"

[azure]
endpoint = "https://<resource>.openai.azure.com"
deployment = "<deployment-name>"
api_key = "<api-key>"
```

### Connection errors

**401 Unauthorized**
- Verify your API key is correct
- Check that the key has access to the specified deployment
- For Key Vault: ensure your Azure identity has `Get` permission on secrets

**404 Not Found**
- Check the endpoint URL format
- Verify the deployment name exists in your Azure resource
- Ensure the API version is supported

**429 Too Many Requests**
- You've hit rate limits; wait and retry
- Consider implementing request throttling

**Timeout errors**
- Check network connectivity
- Verify the endpoint is accessible from your network
- Try increasing timeout if using a slow connection

### Diagnostic commands

```bash
# Test configuration and connectivity
crowelogic doctor run

# Show current configuration (masks API keys)
crowelogic config show

# Show where config files are searched
crowelogic config path
```

## Development

### Install dev dependencies

```bash
pip install -e ".[dev]"
```

### Run tests

```bash
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest --cov              # With coverage report
pytest tests/test_config.py  # Run specific test file
```

### Code quality

```bash
# Type checking
mypy src/crowe_logic_cli

# Linting
ruff check src/crowe_logic_cli

# Format check
ruff format --check src/crowe_logic_cli
```

## Notes

- This project is intentionally minimal; add commands as your org's workflows solidify.
- You can pair this with the repository's existing plugin content (agents/commands/hooks) as source material, but this CLI is designed to run independently.
- Add `.crowelogic.toml` to your `.gitignore` to avoid committing API keys.
