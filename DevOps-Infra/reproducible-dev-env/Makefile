# D5 — reproducible dev environment.
# The single bootstrap command for a fresh clone is:  make
.DEFAULT_GOAL := bootstrap

.PHONY: bootstrap test run doctor clean help

bootstrap:        ## Install pinned toolchain, venv, deps, then run tests (fresh-clone entrypoint)
	@./scripts/bootstrap.sh

test:             ## Run the test suite in the existing venv
	@./.venv/bin/python -m pytest -q

run:              ## Run the service locally on :8000
	@./.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

doctor:           ## Show the resolved pinned toolchain
	@mise ls

clean:            ## Remove the virtualenv
	@rm -rf .venv && echo "removed .venv"

help:             ## List targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-12s %s\n", $$1, $$2}'
