# Crowe Logic CLI - Quick Start Guide

## Installation

```bash
cd ~/claude-code/code/crowe-logic-cli
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## First-Time Setup

Run the interactive configuration wizard:

```bash
crowelogic config run
```

This will guide you through:
1. **Provider Selection**: Choose your AI provider
   - Azure AI Inference (for Claude via Azure AI Foundry)
   - Azure OpenAI (for GPT models)
   - OpenAI-compatible (for other endpoints)

2. **Credentials**: Enter your endpoint URL, model name, and API key

3. **Azure Key Vault** (optional): Store secrets securely

4. **Connection Test**: Automatically verify your setup

### Manual Configuration

Alternatively, create `~/.crowelogic.toml`:

```toml
provider = "azure_ai_inference"

[azure_ai_inference]
endpoint = "https://your-resource.cognitiveservices.azure.com"
model = "claude-opus-4-5"
api_key = "your-api-key"
api_version = "2024-05-01-preview"
```

## Basic Usage

### Test Your Connection

```bash
crowelogic doctor run
```

If you see errors, the diagnostic output will suggest fixes.

### Single-Shot Chat

```bash
crowelogic chat run "Explain quantum computing in simple terms"
```

### Interactive Chat (Recommended)

```bash
crowelogic interactive run
```

**Features:**
- Real-time streaming responses
- Token usage tracking
- Save conversations with `/save <name>`
- Clear history with `/clear`
- Exit with `/exit` (shows session totals)

**Example session:**

```
You: How do I implement a binary tree in Python?
Assistant: [detailed explanation with code]
Tokens: 15 in / 342 out / 357 total

You: What about balancing it?
Assistant: [explanation of AVL/Red-Black trees]
Tokens: 8 in / 289 out / 297 total

You: /save binary-tree-tutorial
✓ Conversation saved as 'binary-tree-tutorial'

You: /exit
Session Summary:
  Total tokens: 654 (23 in / 631 out)
Goodbye!
```

### Resume Saved Conversations

```bash
# List saved conversations
crowelogic history list

# Resume where you left off
crowelogic history resume binary-tree-tutorial
```

The assistant will have full context from the previous session.

### Run Agents

Agents are specialized prompts from the plugins directory.

```bash
# List available agents
crowelogic agent list

# Run an agent
crowelogic agent run code-reviewer "Review this function: def add(a,b): return a+b"
```

## Common Workflows

### Code Review Workflow

```bash
# Start interactive session with code reviewer agent
crowelogic agent run code-reviewer "I need help reviewing my pull request"

# Or use interactive mode with a custom system prompt
crowelogic interactive run --system "You are an expert code reviewer"
```

### Learning Session

```bash
# Start interactive session
crowelogic interactive run

# Ask questions, get explanations
You: Explain decorators in Python
Assistant: [detailed explanation]

You: Show me an example
Assistant: [code example]

# Save for future reference
You: /save python-decorators
```

### Troubleshooting

If you encounter connection errors:

```bash
# Run diagnostics
crowelogic doctor run
```

The output will provide specific suggestions based on the error:
- **404**: Check endpoint URL and model name
- **401/403**: Verify API key and permissions
- **429**: Rate limit - wait and retry
- **500-503**: Azure service issue - check status page
- **Timeout**: Network connectivity issue

## Azure Key Vault Setup (Recommended for Production)

Store secrets securely instead of in config files:

```bash
# Login to Azure
az login

# Create Key Vault (if needed)
az keyvault create --name my-vault --resource-group my-rg --location eastus

# Store your API key
az keyvault secret set --vault-name my-vault --name claude-api-key --value "your-api-key"

# Grant yourself access
az keyvault set-policy --name my-vault --upn your-email@example.com --secret-permissions get
```

Update your config:

```toml
[azure_ai_inference]
endpoint = "https://your-resource.cognitiveservices.azure.com"
model = "claude-opus-4-5"
api_key = "keyvault://my-vault/claude-api-key"  # 👈 Key Vault reference
api_version = "2024-05-01-preview"
```

## Tips

1. **Use streaming** (default) for better UX - see text as it generates
2. **Save important conversations** with `/save` for future reference
3. **Track token usage** to monitor costs
4. **Use agents** for specialized tasks (code review, architecture, etc.)
5. **Secure your secrets** with Azure Key Vault
6. **Set file permissions** on config: `chmod 600 ~/.crowelogic.toml`

## Next Steps

- Explore available agents: `crowelogic agent list`
- Browse plugins: `crowelogic plugins list`
- Read full feature docs: [FEATURES.md](FEATURES.md)
- Customize agents by creating new `.md` files in `plugins/*/agents/`

## Getting Help

```bash
# Show available commands
crowelogic --help

# Show command-specific help
crowelogic interactive --help
crowelogic agent --help
```
