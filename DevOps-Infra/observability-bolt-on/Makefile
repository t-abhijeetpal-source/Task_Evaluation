# D6 Observability Bolt-On — local developer entrypoint.
.DEFAULT_GOAL := help
SHELL := /bin/bash

VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
COMPOSE := docker compose

.PHONY: help venv test lint typecheck audit check up down load verify clean

help:  ## Show available targets
	@grep -hE '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*## "}{printf "  \033[36m%-12s\033[0m %s\n",$$1,$$2}'

$(VENV):  ## Create the virtualenv + install dev deps
	python3 -m venv $(VENV)
	$(PIP) install -q --upgrade pip
	$(PIP) install -q -r requirements-dev.txt

venv: $(VENV)  ## Alias: ensure the venv exists

test: $(VENV)  ## Run pytest with the coverage gate (--cov-fail-under=80)
	$(PY) -m pytest

lint: $(VENV)  ## ruff lint + format check
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .

typecheck: $(VENV)  ## mypy --strict on app/
	$(VENV)/bin/mypy app --strict

audit: $(VENV)  ## pip-audit the runtime dependencies
	$(VENV)/bin/pip-audit -r requirements.txt

check: lint typecheck test  ## All offline gates: lint + types + tests/coverage

up:  ## Build + start the demo stack (app + prometheus + alertmanager + grafana)
	$(COMPOSE) up -d --build

down:  ## Stop + remove the stack (containers, network, volumes)
	$(COMPOSE) down -v

load:  ## Generate a mixed-traffic load run against the local app
	./scripts/generate-load.sh http://localhost:8000 600 20

verify:  ## Full end-to-end stack verification (requires docker)
	./scripts/verify-stack.sh

clean:  ## Remove venv + caches
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .coverage
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
