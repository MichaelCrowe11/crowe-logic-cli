# Crowe Logic CLI - Features Documentation

## Recently Added (Latest Session)

### 🎯 Configuration Wizard
**Command:** `crowelogic config run`

Guided setup for first-time users:
- Provider selection (Azure AI Inference, Azure OpenAI, OpenAI-compatible)
- Interactive credential entry
- Optional Azure Key Vault integration
- Automatic connection testing
- Configuration preview and overwrite protection

### 💾 Conversation History
**Commands:** `crowelogic history list|load|resume|delete`

Save and resume chat sessions:
- Type `/save <name>` in interactive mode
- Resume sessions with full context
- JSON storage in `~/.crowelogic/history/`
- List, load, and delete saved conversations

### 🔍 Enhanced Error Diagnostics
**Command:** `crowelogic doctor run`

Intelligent error troubleshooting:
- Pattern matching for common errors (404, 401, 429, 500, timeout)
- Azure-specific suggestions
- Key Vault credential help
- Service status links

### 📊 Token Usage Tracking

Automatic cost visibility:
- Per-response token counts (input/output/total)
- Session totals on exit
- Works in streaming and non-streaming modes
- Currently supported for Azure AI Inference (Anthropic format)

---

# Crowe Logic CLI - New Features Summary

## ✅ Implemented Features

### 1. Streaming Responses

Text now appears as it's generated (instead of waiting for the full response).

**Usage:**
```bash
# Interactive mode uses streaming by default
crowelogic interactive run

# Disable streaming if needed
crowelogic interactive run --no-stream
```

**Technical details:**
- Added `chat_stream()` method to provider interface
- Azure AI Inference provider supports Server-Sent Events (SSE)
- Graceful fallback to non-streaming if not supported

---

### 2. Agent Runner

Execute agent markdown files from the plugins directory as structured prompts.

**Usage:**
```bash
# List available agents
crowelogic agent list

# Run an agent
crowelogic agent run code-reviewer "Review this implementation"

# Run agent with file context
crowelogic agent run code-reviewer "Review this" --file src/main.py

# Disable streaming
crowelogic agent run code-reviewer "Review this" --no-stream
```

**How it works:**
- Searches `plugins/*/agents/` for agent markdown files
- Loads agent content as system prompt
- Sends your prompt as user message
- Streams or displays the response

**Available agents** (from this repo):
- `code-reviewer` (pr-review-toolkit)
- `code-simplifier` (pr-review-toolkit)
- `comment-analyzer` (pr-review-toolkit)
- `pr-test-analyzer` (pr-review-toolkit)
- `code-architect` (feature-dev)
- `code-explorer` (feature-dev)
- `conversation-analyzer` (hookify)
- `agent-creator` (plugin-dev)
- `plugin-validator` (plugin-dev)
- `skill-reviewer` (plugin-dev)
- `agent-sdk-verifier-py` (agent-sdk-dev)
- `agent-sdk-verifier-ts` (agent-sdk-dev)

---

### 3. Azure Key Vault Integration

Store secrets in Azure Key Vault instead of config files.

**Setup:**
```bash
# 1. Create a Key Vault (if you don't have one)
az keyvault create --name my-vault --resource-group my-rg --location eastus

# 2. Store your API key
az keyvault secret set --vault-name my-vault --name crowe-api-key --value "YOUR_API_KEY"

# 3. Ensure you're authenticated
az login

# 4. Update your config file
```

**Config file with Key Vault** (`~/.crowelogic.toml`):
```toml
provider = "azure_ai_inference"

[azure_ai_inference]
endpoint = "https://ai-michael9466ai832340755092.cognitiveservices.azure.com"
model = "claude-opus-4-5"
# Reference Key Vault secret instead of storing key directly
api_key = "keyvault://my-vault/crowe-api-key"
api_version = "2024-05-01-preview"
```

**How it works:**
- Format: `keyvault://<vault-name>/<secret-name>`
- Uses `DefaultAzureCredential` (respects `az login`, managed identity, service principal, etc.)
- Secrets are fetched on startup
- Falls back to direct values if not a `keyvault://` reference

**Benefits:**
- API keys never stored in plain text files
- Centralized secret management
- Audit logging (Key Vault tracks all access)
- RBAC controls who can read secrets
- Production-ready security

---

## Quick Start

### Test streaming in interactive mode
```bash
cd ~/claude-code/code/crowe-logic-cli
source .venv/bin/activate
crowelogic interactive run
```

### Run a code review agent
```bash
crowelogic agent list
crowelogic agent run code-reviewer "Review the implementation in this file" --file path/to/file.py
```

### Use Key Vault (optional but recommended)
```bash
# Store your API key in Key Vault
az keyvault secret set --vault-name YOUR_VAULT --name crowe-api-key --value "YOUR_API_KEY"

# Update ~/.crowelogic.toml
nano ~/.crowelogic.toml
# Change: api_key = "keyvault://YOUR_VAULT/crowe-api-key"

# Test
crowelogic doctor run
```

---

## Dependencies Added

The following packages were added to support these features:

```toml
dependencies = [
  "httpx-sse>=0.4.0",              # For streaming responses
  "azure-keyvault-secrets>=4.7.0", # For Key Vault integration
  "azure-identity>=1.15.0",        # For Azure authentication
]
```

---

## All Available Commands

```bash
crowelogic --help                 # Show all commands
crowelogic version               # Show version

# Configuration & connectivity
crowelogic doctor run            # Test endpoint connection

# Chat modes
crowelogic chat run "prompt"     # Single-shot prompt
crowelogic interactive run       # Multi-turn conversation (streaming)
crowelogic interactive run --no-stream  # Disable streaming

# Agent execution
crowelogic agent list            # List available agents
crowelogic agent run <name> "prompt"    # Run agent
crowelogic agent run <name> "prompt" --file code.py  # Run with file context

# Discovery
crowelogic plugins list          # List all plugins
crowelogic plugins show hookify  # Show plugin details
```

---

## Security Best Practices

1. **Use Key Vault for production**
   - Never commit API keys to git
   - Store secrets in Key Vault
   - Add `~/.crowelogic.toml` to `.gitignore`

2. **Rotate keys regularly**
   ```bash
   # Generate new key in Azure Portal
   # Update Key Vault
   az keyvault secret set --vault-name my-vault --name crowe-api-key --value "NEW_KEY"
   # CLI picks up new key on next run
   ```

3. **Use managed identity in Azure VMs/containers**
   - DefaultAzureCredential automatically uses managed identity
   - No need for `az login` or service principal secrets
