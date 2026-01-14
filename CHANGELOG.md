# Changelog

All notable changes to Crowe Logic CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-13

### Added
- **Core CLI Framework**
  - Interactive multi-turn chat with streaming responses
  - Configuration wizard for easy setup
  - Doctor command for connectivity diagnostics
  - Conversation history management (save/resume sessions)

- **Azure Integration**
  - Azure AI Inference provider (Claude Opus 4.5)
  - Azure OpenAI provider support
  - Azure Key Vault integration for secure credential storage
  - OpenAI-compatible endpoint support

- **Quantum-Enhanced Reasoning** (`crowelogic quantum`)
  - Crowe Logic 4-stage reasoning framework
  - VQE (Variational Quantum Eigensolver) inspired calculations
  - QAOA (Quantum Approximate Optimization Algorithm) conformer optimization
  - Quantum kernel molecular similarity

- **Molecular Dynamics** (`crowelogic molecular`)
  - CriOS Nova platform integration
  - PubChem compound validation
  - Molecular structure analysis

- **Scientific Research** (`crowelogic research`)
  - Research paper review with specialized agents
  - Molecular structure reviewer
  - Methodology validator
  - Citation checker

- **Code Analysis** (`crowelogic code`)
  - Code explanation (Claude Code style)
  - Code review with quality assessment
  - Fix suggestions
  - Test generation
  - Workspace context queries

- **Plugin System**
  - Agent discovery and execution
  - Plugin listing and inspection
  - Extensible command architecture

### Security
- Apache 2.0 license with patent protection
- Secure credential storage via config files
- Azure Key Vault integration option

---

## [Unreleased]

### Planned
- Web UI (Azure Static Web Apps)
- VS Code extension
- Docker containerization
- Homebrew formula
- Additional quantum algorithms

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| 1.0.0 | 2026-01-13 | Initial release with full feature set |

---

## Migration Guide

### From Development to v1.0.0

If you were using the development version:

```bash
# Uninstall old version
pip uninstall crowe-logic-cli

# Install v1.0.0
pip install crowe-logic-cli==1.0.0

# Or from source
pip install -e .
```

No configuration changes required - existing `~/.crowelogic.toml` files are compatible.
