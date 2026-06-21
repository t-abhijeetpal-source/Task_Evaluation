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

# Self-contained I3 "smallest safe change" sandbox (seeded date-parser bug + proof).
I3_SANDBOX := "Intermediate/minimal-safe-change/sandbox"

# I1 ER-diagram task (artifact validator + spec-sync guard; no live repo required).
I1_DIR := "Intermediate/er-diagram"

.PHONY: help bootstrap doctor setup-env verify test rust node python i1-verify i3-verify i3-flutter-verify a3-integration clean

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
test: rust node python i3-verify i1-verify  ## Run every test suite (Rust + Node + Python + I3 sandbox + I1 ER diagram)
	@echo "== ALL SUITES PASSED =="

# ---- I1 — ER-diagram artifact (validator + tests + spec-sync; offline) ---------
i1-verify:  ## Verify the I1 ER-diagram artifact (pytest + validator + Prisma fixture + spec-sync guard)
	@echo "== i1: $(I1_DIR) =="
	@( cd $(I1_DIR) && $(RUN) python -m venv .venv && . .venv/bin/activate \
		&& pip -q install -r requirements.txt \
		&& python -m pytest -v \
		&& python scripts/validate_er_diagram.py \
		&& python scripts/validate_er_diagram.py --stack prisma --prisma tests/fixtures/prisma-sample/schema.prisma ) || exit 1
	@bash "Intermediate/er-diagram/scripts/check_spec_sync.sh"

# ---- I3 — smallest safe change (self-contained sandbox) ------------------------
i3-verify:  ## Verify the I3 safe-change sandbox (pytest + ruff + spec-sync guard)
	@echo "== i3: $(I3_SANDBOX) =="
	@( cd $(I3_SANDBOX) && $(RUN) python -m venv .venv && . .venv/bin/activate \
		&& pip -q install -r requirements.txt ruff \
		&& python -m pytest -v && ruff check . ) || exit 1
	@bash "Intermediate/minimal-safe-change/scripts/check-i3-sync.sh"

i3-flutter-verify:  ## (Optional) Run the extended Flutter proof; skips cleanly if flutter is absent
	@if command -v flutter >/dev/null 2>&1; then \
		echo "== i3 flutter (extended) =="; \
		echo "See Intermediate/minimal-safe-change/docs/agent-analysis/I3_safe_change.md for the pml-flutter steps."; \
	else \
		echo "== i3 flutter (extended): SKIPPED — flutter SDK not found (optional, not required for bootstrap) =="; \
	fi

a3-integration:  ## Run the A3 polyglot end-to-end integration test
	@bash "Advanced/polyglot-fraud-system/integration-tests/run_integration.sh"

clean:  ## Remove generated venvs / node_modules / build artifacts
	@find . -type d \( -name .venv -o -name node_modules -o -name target \
		-o -name __pycache__ -o -name .pytest_cache -o -name runtime -o -name .run \) \
		-prune -exec rm -rf {} + 2>/dev/null || true
	@echo "cleaned"
