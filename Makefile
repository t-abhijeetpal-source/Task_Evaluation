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

# I4 polyglot currency pair (FastAPI service + Node CLI, shared currency_core).
I4_DIR := "Intermediate/polyglot-currency-pair"

# A2 parallel expense tracker (FastAPI + SQLite + vanilla JS + Docker).
A2_DIR := "Advanced/parallel-expense-tracker"

# A1 parallel-repo-analysis (multi-agent analysis reports + validator; offline, no target repo).
A1_DIR := "Advanced/parallel-repo-analysis"

# A6 performance optimization (profiles + optimizes A2's GET /api/summary).
A6_DIR := "Advanced/performance-optimization"

# A3 polyglot fraud system (FastAPI + Node worker + Rust engine; file-queue + HTTP callback).
A3_DIR := Advanced/polyglot-fraud-system

# Basics tier — shared contract + analysis artifact gates.
BASICS_DIR := Basics

# D5 reproducible dev environment (self-contained FastAPI demo; its own pinned mise.toml).
D5_DIR := DevOps-Infra/reproducible-dev-env

# D1 terraform-aws-stack (S3 + Lambda + API GW HTTP v2; offline plan, no AWS account).
D1_DIR := DevOps-Infra/terraform-aws-stack

.PHONY: help bootstrap doctor setup-env verify test rust node python i1-verify i3-verify i3-flutter-verify i4-verify a1-validate a2-verify a2-docker-smoke a3-integration a3-verify a6-verify agent-platform basics-verify b1-verify b2-verify b3-verify basics-build-test b6-bench d5-verify d1-verify clean

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
test: rust node python i3-verify i1-verify i4-verify d5-verify d1-verify  ## Run every test suite (Rust + Node + Python + I3 sandbox + I1 ER diagram + I4 polyglot pair + D5 reproducible env + D1 terraform)
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

# ---- I4 — polyglot currency pair (core + service + client + live integration) -
i4-verify:  ## Verify I4 polyglot pair (currency_core + service pytest + client jest + live integration + perf gate)
	@echo "== i4: $(I4_DIR) =="
	@( cd $(I4_DIR)/fastapi-service && $(RUN) python -m venv .venv && . .venv/bin/activate \
		&& pip -q install -r requirements.txt \
		&& echo "-- shared currency_core tests --" && python -m pytest -q ../../shared/currency-core/tests \
		&& echo "-- service tests --" && python -m pytest -q \
		&& echo "-- perf gate: p50 POST /convert < 10ms --" && python bench_convert.py ) || exit 1
	@echo "-- client tests --"
	@( cd $(I4_DIR)/node-client && $(RUN) npm install --silent && $(RUN) npm test ) || exit 1
	@echo "-- live integration: 6 rate pairs + 4 exit codes over real HTTP --"
	@$(RUN) bash "Intermediate/polyglot-currency-pair/integration-tests/run_integration.sh"

# ---- A2 — parallel expense tracker (one-command production-grade verify) -------
a2-verify:  ## Verify A2 (pytest + live HTTP integration + frontend smoke + A6 perf gate; A2_DOCKER=1 also runs docker smoke)
	@echo "== a2: $(A2_DIR) =="
	@( cd $(A2_DIR) && $(RUN) python -m venv .venv && . .venv/bin/activate \
		&& pip -q install --upgrade pip >/dev/null \
		&& pip -q install -r requirements-dev.txt \
		&& echo "-- pytest (>=24 tests) --" && python -m pytest -q \
		&& echo "-- frontend smoke: node --check static/app.js --" \
		&& if command -v node >/dev/null 2>&1; then node --check static/app.js && echo "  app.js OK"; \
		   else echo "  node not found — skipping JS syntax check"; fi \
		&& echo "-- live HTTP integration smoke --" && PYTHON=python bash scripts/integration_smoke.sh \
		&& echo "-- perf gate: p50 GET /api/summary (A6 linkage) --" && python scripts/perf_guard.py ) || exit 1
	@if [ "$${A2_DOCKER:-0}" = "1" ]; then \
		$(MAKE) a2-docker-smoke; \
	else \
		echo "-- docker smoke: SKIPPED (run 'A2_DOCKER=1 make a2-verify' or 'make a2-docker-smoke') --"; \
	fi
	@echo "== ✅ A2 VERIFY PASSED =="

a2-docker-smoke:  ## Build the A2 image, run it, wait for healthy, exercise the API, tear down (skips cleanly if docker absent)
	@bash $(A2_DIR)/scripts/docker_smoke.sh

# ---- A6 — performance optimization (validate deliverable + live bench on 3.12) -
a6-verify:  ## Verify A6 (deliverable validation + pytest + compare-before bench + perf gate, Python 3.12)
	@echo "== a6: $(A6_DIR) =="
	@bash $(A6_DIR)/scripts/validate_a6_deliverable.sh
	@( cd $(A2_DIR) && $(RUN) python -m venv .venv && . .venv/bin/activate \
		&& pip -q install --upgrade pip >/dev/null \
		&& pip -q install -r requirements-dev.txt \
		&& echo "-- behavior preserved: pytest --" && python -m pytest -q \
		&& echo "-- compare-before: naive ORM vs SQL GROUP BY --" \
		&& python ../performance-optimization/bench_summary.py --compare-before \
		&& echo "-- perf gate: p50 GET /api/summary <= ceiling --" && python scripts/perf_guard.py ) || exit 1
	@echo "== ✅ A6 VERIFY PASSED =="

# ---- A1 — parallel repo analysis (validate deliverables; offline, no target repo) -
a1-validate:  ## Validate the A1 parallel-repo-analysis deliverables (9 reports + structure/content gate)
	@echo "== a1: $(A1_DIR) =="
	@bash $(A1_DIR)/scripts/validate_a1_reports.sh
	@bash $(A1_DIR)/run_a1_analysis.sh --validate-only
	@echo "== ✅ A1 VALIDATE PASSED =="

a3-integration:  ## Run the A3 polyglot end-to-end integration test
	@bash "$(A3_DIR)/integration-tests/run_integration.sh"

# ---- A3 — polyglot fraud system (full one-command verify) ----------------------
a3-verify:  ## Verify A3 (Rust + pytest + Node + contract conformance + e2e integration + deliverable gate; regenerates evidence)
	@echo "== a3: $(A3_DIR) =="
	@echo "-- Rust engine: build --release + cargo test --"
	@( cd $(A3_DIR)/rust-engine && $(RUN) cargo build --release && $(RUN) cargo test ) || exit 1
	@echo "-- FastAPI: venv + pytest --"
	@( cd $(A3_DIR)/fastapi-service && $(RUN) python -m venv .venv && . .venv/bin/activate \
		&& pip -q install --upgrade pip >/dev/null && pip -q install -r requirements.txt \
		&& python -m pytest -q ) || exit 1
	@echo "-- Node worker: install + jest --"
	@( cd $(A3_DIR)/node-worker && $(RUN) npm install --silent && $(RUN) npm test ) || exit 1
	@echo "-- Contract conformance: 4 canonical vectors through the engine --"
	@( cd $(A3_DIR) && $(RUN) bash scripts/contract_conformance.sh )
	@echo "-- Capture evidence + regenerate VERIFICATION_RESULTS.md (runs e2e integration) --"
	@# cd into A3 so `mise exec` resolves the A3 mise.toml pins (Node 26.3.0 / Rust 1.96.0),
	@# not the monorepo-root pins — the captured evidence must reflect THIS component's toolchain.
	@( cd $(A3_DIR) && $(RUN) bash scripts/capture_verification.sh )
	@echo "-- Deliverable validation gate (structure + doc consistency) --"
	@( cd $(A3_DIR) && bash scripts/validate_a3_deliverable.sh )
	@echo "== ✅ A3 VERIFY PASSED =="

# ---- agent-platform — Next.js showcase (data integrity + build) ----------------
agent-platform:  ## Verify the Next.js agent-platform (regenerate metrics -> test -> lint -> build)
	@echo "== agent-platform: install + verify =="
	@( cd agent-platform \
		&& npm ci \
		&& echo "-- regenerate metrics.json from real repo data --" && npm run build:metrics \
		&& echo "-- node:test suite --" && npm test \
		&& echo "-- eslint --" && npm run lint \
		&& echo "-- next build --" && npm run build ) || exit 1
	@echo "== ✅ AGENT-PLATFORM PASSED =="

# ---- D5 reproducible dev environment (self-contained; own pinned mise.toml) ----
d5-verify:  ## Verify D5 (toolchain-pin sync guard + one-command bootstrap: ruff + mypy + pytest --cov)
	@echo "== d5: toolchain sync guard =="
	@( cd $(D5_DIR) && ./scripts/check-toolchain-sync.sh ) || exit 1
	@echo "== d5: bootstrap (install -> verify pins -> venv -> deps -> gates -> tests) =="
	@( cd $(D5_DIR) && $(MAKE) bootstrap ) || exit 1
	@echo "== ✅ D5 REPRODUCIBLE-ENV PASSED =="

# ---- D1 terraform-aws-stack (offline plan + handler tests; no AWS account) -----
d1-verify:  ## Verify D1 (terraform fmt/validate/offline-plan + tflint/checkov if present + handler tests)
	@$(RUN) bash $(D1_DIR)/scripts/verify.sh

# ---- Basics — B1–B6 shared contract + artifact gates + service tests -----------
basics-verify: b1-verify b2-verify b3-verify basics-build-test b6-bench  ## Verify Basics tier (B1–B6 artifacts + B4/B5 contract + B6)

b1-verify:  ## Validate B1 inventory artifact (offline section + count checks)
	@bash "$(BASICS_DIR)/scripts/validate_b1_inventory.sh"

b2-verify:  ## Validate B2 route map (offline YAML; live diff when REPO_ROOT is set)
	@bash "$(BASICS_DIR)/scripts/b2-verify.sh"

b3-verify:  ## Validate B3 test-discovery staleness anchors
	@bash "$(BASICS_DIR)/scripts/check_b3_staleness.sh"

basics-build-test:  ## Run B4 (pytest) + B5 (jest) + B6 (cargo) including shared contract tests
	@echo "== basics: rust-logcount-cli =="
	@( cd $(BASICS_DIR)/rust-logcount-cli && $(RUN) cargo test ) || exit 1
	@echo "== basics: node-transaction-service =="
	@( cd $(BASICS_DIR)/node-transaction-service && $(RUN) npm install --silent && $(RUN) npm test ) || exit 1
	@echo "== basics: fastapi-transaction-service =="
	@( cd $(BASICS_DIR)/fastapi-transaction-service && $(RUN) python -m venv .venv && . .venv/bin/activate \
		&& pip -q install -r requirements.txt && python -m pytest -q ) || exit 1
	@echo "== ✅ BASICS VERIFY PASSED =="

b6-bench:  ## Stream-benchmark B6 logcount on a 50k-line temp file
	@bash "$(BASICS_DIR)/scripts/bench_logcount.sh"

clean:  ## Remove generated venvs / node_modules / build artifacts
	@find . -type d \( -name .venv -o -name node_modules -o -name target \
		-o -name __pycache__ -o -name .pytest_cache -o -name runtime -o -name .run \) \
		-prune -exec rm -rf {} + 2>/dev/null || true
	@echo "cleaned"
