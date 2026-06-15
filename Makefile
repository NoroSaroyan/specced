# specced — dev tasks (we eat our own verification-vocabulary dog food).

.DEFAULT_GOAL := help
.PHONY: help install fmt lint test build verify clean

help: ## List available targets
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

install: ## Create the dev environment
	uv venv
	uv pip install -e ".[dev]"

fmt: ## Auto-format
	uv run ruff format src tests

lint: ## Format check + lint
	uv run ruff format --check src tests
	uv run ruff check src tests

test: ## Run the test suite
	uv run pytest

build: ## Build the wheel + sdist
	uv build

verify: lint test build ## Full local gate (mirror of CI)
	@echo "verify: OK"

clean: ## Remove build artifacts and caches
	rm -rf dist build .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
