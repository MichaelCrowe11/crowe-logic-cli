# Crowe Logic CLI - Build and Distribution Makefile
.PHONY: help install dev test lint build clean formula release

PYTHON := python3
VENV := .venv
BIN := $(VENV)/bin
VERSION := $(shell grep -m1 'version' pyproject.toml | cut -d'"' -f2)

help:  ## Show this help message
	@echo "Crowe Logic CLI v$(VERSION) - Build Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ============================================================================
# Development
# ============================================================================

install:  ## Install in editable mode
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install -e .

dev:  ## Install with dev dependencies
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install -e ".[dev,build]"

test:  ## Run tests
	$(BIN)/pytest tests/ -v

lint:  ## Run linting
	$(BIN)/ruff check src/
	$(BIN)/mypy src/

format:  ## Format code
	$(BIN)/ruff format src/

# ============================================================================
# Build
# ============================================================================

build:  ## Build standalone executable with PyInstaller
	$(BIN)/python build_exe.py --clean

build-dir:  ## Build as directory (faster startup)
	$(BIN)/python build_exe.py --clean --onedir

build-debug:  ## Build with debug info
	$(BIN)/python build_exe.py --clean --debug

# ============================================================================
# Homebrew
# ============================================================================

formula:  ## Generate Homebrew formula with real PyPI hashes
	@mkdir -p homebrew-tap/Formula
	$(BIN)/python scripts/generate_formula.py > homebrew-tap/Formula/crowelogic.rb
	@echo "Formula generated: homebrew-tap/Formula/crowelogic.rb"

formula-test:  ## Test Homebrew formula locally
	brew install --build-from-source ./homebrew-tap/Formula/crowelogic.rb

# ============================================================================
# Release
# ============================================================================

dist:  ## Build source distribution
	$(BIN)/python -m build

release-check:  ## Check if ready for release
	@echo "Checking version: $(VERSION)"
	@echo "Checking git status..."
	@git status --short
	@echo ""
	@echo "Run 'make release' when ready"

release:  ## Create a new release (interactive)
	@echo "Creating release v$(VERSION)..."
	@echo "1. Ensure all changes are committed"
	@echo "2. Create and push tag:"
	@echo "   git tag -a v$(VERSION) -m 'Release v$(VERSION)'"
	@echo "   git push origin v$(VERSION)"
	@echo "3. Generate formula with real SHA256:"
	@echo "   make formula"
	@echo "4. Build binaries:"
	@echo "   make build"

# ============================================================================
# Cleanup
# ============================================================================

clean:  ## Clean build artifacts
	rm -rf build/ dist/ *.spec __pycache__/
	rm -rf src/*.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

clean-all: clean  ## Clean everything including venv
	rm -rf $(VENV)