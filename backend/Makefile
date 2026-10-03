# Inbox Copilot backend - developer commands. Run `make` or `make help` to list targets.
.DEFAULT_GOAL := help
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

UV  ?= uv
RUN := $(UV) run
SRC := app tests

##@ Setup
.PHONY: install
install: ## Create venv and install all deps from the lockfile
	$(UV) sync --all-groups

.PHONY: lock
lock: ## Re-resolve dependencies and update uv.lock
	$(UV) lock

.PHONY: upgrade
upgrade: ## Upgrade all dependencies within their constraints
	$(UV) lock --upgrade
	$(UV) sync --all-groups

##@ Run
HOST ?= 127.0.0.1
PORT ?= 8000
APP  := app.main:app

.PHONY: dev
dev: ## Run the API with auto-reload
	$(RUN) uvicorn $(APP) --reload --host $(HOST) --port $(PORT)

.PHONY: run
run: ## Run the API as in production (no reload)
	$(RUN) uvicorn $(APP) --host $(HOST) --port $(PORT)

.PHONY: openapi
openapi: ## Export the OpenAPI spec to ../contract/openapi.json
	$(RUN) python -m app.scripts.export_openapi ../contract/openapi.json

##@ Quality
.PHONY: format
format: ## Auto-format and apply safe lint fixes
	$(RUN) ruff format $(SRC)
	$(RUN) ruff check --fix $(SRC)

.PHONY: format-check
format-check: ## Verify formatting without changing files
	$(RUN) ruff format --check $(SRC)

.PHONY: lint
lint: ## Run ruff linter
	$(RUN) ruff check $(SRC)

.PHONY: typecheck
typecheck: ## Run mypy
	$(RUN) mypy

.PHONY: test
test: ## Run tests
	$(RUN) pytest

.PHONY: cov
cov: ## Run tests with coverage report (fails under threshold)
	$(RUN) pytest --cov --cov-report=term-missing

.PHONY: check
check: format-check lint typecheck test ## Everything CI runs - use before every commit/PR
	$(UV) lock --check

##@ Housekeeping
.PHONY: clean
clean: ## Remove caches and build artifacts
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

.PHONY: help
help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage: make \033[36m<target>\033[0m\n"} \
		/^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } \
		/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)
