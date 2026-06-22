# D2 Docker Compose stack — local developer entrypoint.
.DEFAULT_GOAL := help
SHELL := /bin/bash

VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
COMPOSE := docker compose

.PHONY: help venv lint typecheck test test-api test-worker check \
        build up down e2e verify clean

help:  ## Show available targets
	@grep -hE '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*## "}{printf "  \033[36m%-12s\033[0m %s\n",$$1,$$2}'

$(VENV):  ## Create the virtualenv + install both services' dev deps
	python3 -m venv $(VENV)
	$(PIP) install -q --upgrade pip
	$(PIP) install -q -r api/requirements-dev.txt -r worker/requirements-dev.txt

venv: $(VENV)  ## Alias: ensure the venv exists

lint: $(VENV)  ## ruff lint + format check (api + worker)
	$(VENV)/bin/ruff check api worker
	$(VENV)/bin/ruff format --check api worker

typecheck: $(VENV)  ## mypy --strict on api/app + worker
	$(VENV)/bin/mypy api/app worker/worker.py

test-api: $(VENV)  ## pytest the API (coverage gate ≥90%, DB mocked)
	cd api && ../$(VENV)/bin/python -m pytest

test-worker: $(VENV)  ## pytest the worker (coverage gate ≥90%, DB mocked)
	cd worker && ../$(VENV)/bin/python -m pytest

test: test-api test-worker  ## Run both unit suites (no docker)

check: lint typecheck test  ## All offline gates: lint + types + tests/coverage

build:  ## Build the stack images
	$(COMPOSE) build

up:  ## Build + start the stack (waits for healthy); seeds .env if absent
	@[ -f .env ] || cp .env.example .env
	$(COMPOSE) up -d --build --wait

down:  ## Stop + remove the stack (containers, network, volumes)
	$(COMPOSE) down -v

e2e:  ## Run the end-to-end test against the running stack
	./scripts/integration-test.sh

verify:  ## Full end-to-end stack verification (requires docker)
	./scripts/verify-stack.sh

clean:  ## Remove venv + caches
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache \
		api/.venv api/.pytest_cache worker/.venv worker/.pytest_cache \
		api/.coverage worker/.coverage
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
