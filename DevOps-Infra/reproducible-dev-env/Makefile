# D5 — reproducible dev environment.
# The single bootstrap command for a fresh clone is:  make
.DEFAULT_GOAL := bootstrap

VENV := .venv/bin

.PHONY: bootstrap verify test lint run doctor check-sync verify-fresh lock clean help

bootstrap:        ## Install pinned toolchain, venv, deps, gates, tests (fresh-clone entrypoint)
	@./scripts/bootstrap.sh

verify:           ## Run lint + types + tests in the EXISTING venv (no install) — fast inner loop
	@$(VENV)/ruff check .
	@$(VENV)/ruff format --check .
	@$(VENV)/mypy app
	@$(VENV)/python -m pytest -q

test:             ## Run the test suite (with coverage gate) in the existing venv
	@$(VENV)/python -m pytest -q

lint:             ## Lint + format-check + type-check only
	@$(VENV)/ruff check . && $(VENV)/ruff format --check . && $(VENV)/mypy app

run:              ## Run the service locally on :8000
	@$(VENV)/uvicorn app.main:app --host 0.0.0.0 --port 8000

doctor:           ## Show the resolved pinned toolchain
	@mise ls

check-sync:       ## Fail if root/D5 toolchain pins diverge
	@./scripts/check-toolchain-sync.sh

verify-fresh:     ## Simulate a fresh clone (rsync tracked files -> temp) and run `make` there
	@./scripts/verify-fresh-clone.sh

lock:             ## Regenerate requirements.lock (full resolved closure) from the venv
	@{ echo "# Fully-resolved dependency lock for deterministic installs."; \
	   echo "# Generated from the verified .venv (python 3.12.8) via 'pip freeze'."; \
	   echo "# Direct pins live in requirements*.txt; this captures the exact transitive"; \
	   echo "# closure. Deterministic install:  pip install -r requirements.lock"; \
	   echo "# Regenerate after a dependency bump:  make lock"; \
	   $(VENV)/python -m pip freeze --exclude-editable | grep -viE '^(pip|setuptools|wheel)=='; } > requirements.lock
	@echo "wrote requirements.lock"

clean:            ## Remove the virtualenv
	@rm -rf .venv && echo "removed .venv"

help:             ## List targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-14s %s\n", $$1, $$2}'
