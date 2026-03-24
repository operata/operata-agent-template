.DEFAULT_GOAL := help
.PHONY: help setup check run run-live test lint fmt deploy

PYTHON  ?= python
VENV    := .venv
ACTIVATE := source $(VENV)/bin/activate

help: ## Show available targets
	@echo ""
	@echo "  Agent Template"
	@echo "  =============="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""

setup: ## Create venv, install deps, validate environment
	uv venv $(VENV)
	$(ACTIVATE) && uv pip install -r requirements.txt
	$(ACTIVATE) && uv pip install -e ".[dev]"
	@test -f .env || (cp .env.example .env && echo "Created .env from .env.example — fill in your tokens")
	$(ACTIVATE) && $(PYTHON) scripts/check_env.py

check: ## Validate environment (AWS creds, tokens, dependencies)
	@$(ACTIVATE) && $(PYTHON) scripts/check_env.py

run: ## Run agent in dry-run mode (no external writes)
	$(ACTIVATE) && $(PYTHON) agent.py --dry-run

run-live live: ## Run agent (writes to Slack and external systems)
	$(ACTIVATE) && $(PYTHON) agent.py

test: ## Run tests
	$(ACTIVATE) && $(PYTHON) -m pytest tests/ -v

lint: ## Check code style (ruff)
	$(ACTIVATE) && ruff check . && ruff format --check .

fmt: ## Auto-fix code style
	$(ACTIVATE) && ruff check --fix . && ruff format .

deploy: ## Deploy to Bedrock AgentCore
	$(ACTIVATE) && agentcore deploy
