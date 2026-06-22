# D4 kubernetes-manifests — local developer entrypoint.
# Mirrors the CI gates so `make verify` locally == the `validate` + `manifests`
# jobs in .github/workflows/d4-kubernetes.yml.

.DEFAULT_GOAL := help
SHELL := /bin/bash

VENV := .venv
PY   := $(VENV)/bin/python
PIP  := $(VENV)/bin/pip
CLUSTER ?= d4-cluster

.PHONY: help venv test lint typecheck verify validate deploy verify-e2e down clean

help:  ## Show available targets
	@grep -hE '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*## "}{printf "  \033[36m%-14s\033[0m %s\n",$$1,$$2}'

$(VENV)/bin/activate: requirements-dev.txt
	python3 -m venv $(VENV)
	$(PIP) -q install -r requirements-dev.txt

venv: $(VENV)/bin/activate  ## Create the virtualenv + install dev deps

lint: venv  ## ruff lint + format check
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .

typecheck: venv  ## mypy --strict
	$(VENV)/bin/mypy app --strict

test: venv  ## pytest with coverage gate (>=80%)
	$(PY) -m pytest

verify: lint typecheck test  ## App quality gates: ruff + mypy + pytest/coverage
	@echo "✅ App gates passed (ruff · mypy · pytest cov>=80%)."

validate:  ## Offline manifest validation (kustomize + kubeconform strict + kube-score)
	bash scripts/validate-manifests.sh

deploy:  ## kind E2E: build -> load -> apply -k dev -> rollout -> curl proof
	bash scripts/deploy-and-verify.sh

verify-e2e:  ## kind E2E then tear the cluster down
	bash scripts/deploy-and-verify.sh --teardown

down:  ## Delete the kind cluster
	kind delete cluster --name $(CLUSTER) || true

clean:  ## Remove venv + caches
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .coverage
