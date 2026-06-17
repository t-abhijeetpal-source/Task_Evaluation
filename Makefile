# Task_Eval — reproducible build/test entrypoint across all components.
# Single-command onboarding: `make bootstrap` (runtimes -> deps -> env -> verify).
# Runtimes are pinned by mise.toml; commands run under the pinned toolchain when mise is present.

.DEFAULT_GOAL := help
SHELL := /bin/bash

# Run commands under the mise-pinned toolchain when mise is available; else system tools.
MISE := $(shell command -v mise 2>/dev/null)
ifeq ($(strip $(MISE)),)
  RUN :=
else
  RUN := mise exec --
endif

# Independently-buildable projects (paths quoted: some contain spaces).
PY_PROJECTS   := "Basics/fastapi-transaction-service" "Intermediate/bug-diagnosis" "Advanced/parallel-expense-tracker" "Advanced/polyglot-fraud-system/fastapi-service" "Intermediate/polyglot-currency-pair/fastapi-service"
NODE_PROJECTS := "Basics/node-transaction-service" "Intermediate/polyglot-currency-pair/node-client" "Advanced/polyglot-fraud-system/node-worker"
RUST_PROJECTS := "Basics/rust-logcount-cli" "Advanced/polyglot-fraud-system/rust-engine"

.PHONY: help bootstrap doctor setup-env verify test rust node python a3-integration clean

help:  ## Show available targets
	@grep -hE '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*## "}{printf "  \033[36m%-16s\033[0m %s\n",$$1,$$2}'

# ---- Single-command onboarding -------------------------------------------------
bootstrap: doctor setup-env test  ## Fresh-clone onboarding: runtimes -> deps -> env -> verify
	@echo ""
	@echo "✅ BOOTSTRAP COMPLETE — repository is runnable."

doctor:  ## Install pinned runtimes (mise) + report active versions
	@echo "== toolchain =="
ifneq ($(strip $(MISE)),)
	@mise install
	@mise ls --current | grep -E "python|node|rust" || true
else
	@echo "mise not found — using system runtimes (install mise for exact pins)"
endif
	@echo "python: $$($(RUN) python --version 2>&1)  |  node: $$($(RUN) node --version 2>&1)  |  cargo: $$($(RUN) cargo --version 2>&1 | awk '{print $$1,$$2}')"

setup-env:  ## Instantiate .env from .env.example (no overwrite)
	@if [ -f .env ]; then echo "== .env already present (kept) =="; \
	else cp .env.example .env && echo "== generated .env from .env.example =="; fi

# ---- Per-language build + verify (deps installed from lockfiles) ---------------
rust:  ## Build + test all Rust crates (B6, A3 engine)
	@for d in $(RUST_PROJECTS); do echo "== rust: $$d =="; ( cd "$$d" && $(RUN) cargo test ) || exit 1; done

node:  ## Install + test all Node projects (B5, I4 client, A3 worker)
	@for d in $(NODE_PROJECTS); do echo "== node: $$d =="; ( cd "$$d" && $(RUN) npm install --silent && $(RUN) npm test ) || exit 1; done

python:  ## Create venv + install + test all Python services
	@for d in $(PY_PROJECTS); do echo "== python: $$d =="; \
		( cd "$$d" && $(RUN) python -m venv .venv && . .venv/bin/activate \
			&& pip -q install -r requirements.txt && python -m pytest -q ) || exit 1; done

verify: test  ## Alias for the full test suite
test: rust node python  ## Run every test suite (Rust + Node + Python)
	@echo "== ALL SUITES PASSED =="

a3-integration:  ## Run the A3 polyglot end-to-end integration test
	@bash "Advanced/polyglot-fraud-system/integration-tests/run_integration.sh"

clean:  ## Remove generated venvs / node_modules / build artifacts
	@find . -type d \( -name .venv -o -name node_modules -o -name target \
		-o -name __pycache__ -o -name .pytest_cache -o -name runtime -o -name .run \) \
		-prune -exec rm -rf {} + 2>/dev/null || true
	@echo "cleaned"
