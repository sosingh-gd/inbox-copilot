# Inbox Copilot - one entry point for both apps. Run `make` to list targets.
.DEFAULT_GOAL := help
SHELL := /bin/bash

.PHONY: install
install: ## Install backend and frontend dependencies
	$(MAKE) -C backend install
	cd frontend && npm install

.PHONY: dev
dev: ## Run backend (:8000) and frontend (:5173) together; open http://localhost:5173
	@trap 'kill 0' EXIT; \
	$(MAKE) -C backend dev & \
	(cd frontend && npm run dev) & \
	wait

.PHONY: api
api: ## Export the OpenAPI contract and regenerate frontend types (run after backend schema changes)
	$(MAKE) -C backend openapi
	cd frontend && npm run api:gen

.PHONY: api-check
api-check: api ## Fail if the committed contract or generated types are stale
	git diff --exit-code contract/openapi.json frontend/src/lib/api/schema.d.ts || \
	  (echo "API contract out of date: run 'make api' and commit" && exit 1)

.PHONY: format
format: ## Auto-format both apps
	$(MAKE) -C backend format
	cd frontend && npm run format

.PHONY: check
check: ## Formatting, lint, type checks and contract drift for both apps
	$(MAKE) -C backend check
	cd frontend && npm run check
	$(MAKE) api-check

.PHONY: help
help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage: make \033[36m<target>\033[0m\n\n"} \
		/^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
