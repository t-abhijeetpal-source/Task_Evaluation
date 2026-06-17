# D3 CI Pipeline Validation Record

> Production-grade GitHub Actions pipeline for a sample FastAPI service, executed and proven.
> Workflow: `.github/workflows/ci.yml` (repo root). App under test: `Devops & Infra/D3/`.
> Execution evidence below is from the **local runner** (`scripts/run-ci-local.sh`) which runs the
> **identical stage commands** as the workflow, plus a real `docker build`, including the mandatory
> failure→fix cycle. Date: 2026-06-17.

## 1. Pipeline Architecture

### Platform
**GitHub Actions** (`.github/workflows/ci.yml`). Verified locally (see §5–§8). Note on `act`: the
local `act` runner started the job and ran `actions/checkout` successfully, but `actions/setup-python`
could not download Python **inside the runner container** because the corporate TLS proxy isn't
trusted there (`unable to get local issuer certificate`) — an environment limitation of local act,
not a workflow defect. GitHub-hosted runners (no corporate proxy) are unaffected. The captured
evidence therefore uses the command-level local runner, which executes the same commands the
workflow defines.

### Triggers
`on: push`, `pull_request`, `workflow_dispatch` — runs on every push and PR (and manual dispatch).
`concurrency` cancels superseded runs on the same ref.

### Cache Strategy
* **pip:** `actions/setup-python@v5` with `cache: pip` and `cache-dependency-path:
  "Devops & Infra/D3/requirements-dev.txt"` — restores the pip download cache keyed on the lockfile
  hash across runs (cache miss on first run, cache hit thereafter while the lock is unchanged).
* **Docker layers:** the container job uses `cache-from/to: type=gha` (BuildKit GitHub cache).
  **Demonstrated locally:** stage 5 `docker build` took **16s** on first build and **1s** on the
  immediate rebuild — a layer-cache hit (deps layer reused).

### Dependency Strategy
Deterministic, lockfile-based: pinned, frozen versions in `requirements.txt` (runtime — used by the
Dockerfile) and `requirements-dev.txt` (runtime + test/lint/build tooling — used by CI), installed
with `pip install -r requirements-dev.txt` (no floating ranges, no `--upgrade`). Pins were generated
by installing and freezing exact versions (e.g. `fastapi==0.137.1`, `ruff==0.15.17`, `pytest==9.1.0`).

---

## 2. Workflow Manifest

### Pipeline Configuration
```yaml
name: D3 CI
on:
  push:
  pull_request:
  workflow_dispatch:
concurrency:
  group: d3-ci-${{ github.ref }}
  cancel-in-progress: true
defaults:
  run:
    working-directory: "Devops & Infra/D3"
env:
  PYTHON_VERSION: "3.12"
  DEV_LOCK: "Devops & Infra/D3/requirements-dev.txt"

jobs:
  lint:                       # Stage 1 (parallel with unit-tests)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12", cache: pip, cache-dependency-path: "${{ env.DEV_LOCK }}" }
      - run: pip install -r requirements-dev.txt
      - run: ruff check .
      - run: ruff format --check .

  unit-tests:                 # Stage 2 (parallel with lint)
    runs-on: ubuntu-latest
    steps: [checkout, setup-python+cache, pip install -r requirements-dev.txt,
            python -m pytest tests/test_unit.py -v]

  integration-tests:         # Stage 3 (needs unit-tests -> fail fast)
    needs: [unit-tests]
    runs-on: ubuntu-latest
    steps: [..., python -m pytest tests/test_integration.py -v]

  build:                      # Stage 4 + Stage 6 artifact (needs lint + integration)
    needs: [lint, integration-tests]
    runs-on: ubuntu-latest
    steps:
      - ... python -m compileall app
      - build-info.json (commit/run/ref/built_at)        # build metadata
      - zip d3-app-${run}.zip app requirements.txt build-info.json
      - uses: actions/upload-artifact@v4                  # artifact publication (retention 7d)

  container:                  # Stage 5 (needs build)
    needs: [build]
    runs-on: ubuntu-latest
    steps:
      - uses: docker/setup-buildx-action@v3
      - uses: docker/build-push-action@v6
        with: { context: "Devops & Infra/D3", push: false, load: true,
                tags: "d3-sample:${{ github.sha }}\nd3-sample:latest",
                cache-from: type=gha, cache-to: type=gha,mode=max }
```
(Full file in `.github/workflows/ci.yml`.)

---

## 3. Stage Definitions

### Lint
* **Purpose:** style + static checks. **Tools:** `ruff check`, `ruff format --check`.
* **Success Criteria:** zero lint errors, code is formatted. (Parallel with unit tests.)

### Unit Tests
* **Purpose:** verify pure logic (`app/calc.py`). **Commands:** `pytest tests/test_unit.py -v`.
* **Success Criteria:** all unit tests pass.

### Integration Tests
* **Purpose:** verify the API end-to-end (FastAPI `TestClient` hitting `/health`, `/add`).
* **Commands:** `pytest tests/test_integration.py -v`. **Success Criteria:** all pass; depends on unit (fail-fast).

### Build
* **Purpose:** compile-check + produce a versioned, retained artifact with build metadata.
* **Commands:** `python -m compileall app`; write `build-info.json`; `zip` → `upload-artifact`.
* **Success Criteria:** compiles; artifact `d3-app-<run>.zip` published (retention 7 days).

### Container Build
* **Purpose:** validate the Dockerfile and produce a tagged image (no push).
* **Commands:** `docker build` via `docker/build-push-action` (`push:false`, `load:true`, gha cache).
* **Success Criteria:** image `d3-sample:<sha>` + `:latest` builds successfully.

---

## 4. Cache Verification
* **Cache Configuration:** pip cache via `setup-python` (key = hash of `requirements-dev.txt`); docker
  layer cache via `type=gha`.
* **Cache Hit/Miss Evidence (local docker layer cache):**
  ```text
  stage '5-container' (first build)  duration=16s   # cold — installs deps layer
  stage '5-container' (rebuild)      duration=1s    # warm — layer cache hit
  ```
* **Performance Impact:** the dependency layer rebuild dropped from ~16s to ~1s (~16× faster) on a
  warm cache; on GitHub the pip + gha caches give the same effect across separate runs.

---

## 5. Failure Demonstration
**Intentional Failure:** changed `tests/test_unit.py` `assert add(2, 3) == 5` → `== 6`.
**Pipeline Output / Failure Logs:**
```text
===== STAGE: 1-lint =====            ... exit=0
===== STAGE: 2-unit =====
>       assert add(2, 3) == 6  # INTENTIONAL FAILURE
E       assert 5 == 6
E        +  where 5 = add(2, 3)
FAILED tests/test_unit.py::test_add - assert 5 == 6
1 failed, 2 passed
----- stage '2-unit' exit=1 -----
❌ PIPELINE FAILED at stage: 2-unit (exit 1) — downstream stages skipped (fail-fast)
```
**Exit Code:** `1`. **Failure Stage:** Stage 2 (Unit Tests). **Failure Reason:** assertion failure
(`5 != 6`). Stages 3–5 were **not run** (fail-fast gate) — proving broken code is blocked before
build/container/merge.

## 6. Successful Run Demonstration
**Fixed Commit:** reverted the assertion to `== 5`.
**Pipeline Output (all stages):**
```text
STAGE 1-lint        exit=0   All checks passed!
STAGE 2-unit        exit=0   3 passed
STAGE 3-integration exit=0   2 passed
STAGE 4-build       exit=0   artifact: d3-app-6c92fc9.zip
STAGE 5-container   exit=0   sha256:c180ff50a9dd...
✅ ALL STAGES PASSED
```
**Successful Stages:** 1–5 (+ artifact). **Build Duration:** whole local pipeline ≈ a few seconds
(+ first container build 16s). **Artifacts Generated:** `d3-app-<sha>.zip` (app + requirements + build-info.json).

## 7. Container Build Verification
**Docker Build Command:** `docker build -t d3-sample:<sha> -t d3-sample:latest .` (from `Devops & Infra/D3`).
**Logs:**
```text
stage '5-container' ... sha256:c180ff50a9dd0ec04e6ce447de9c0824a39b448add4425609729324449eaf539
----- stage '5-container' exit=0 duration=16s -----   # rebuild: 1s (cache hit)
```
**Image Tag:** `d3-sample:<git-sha>` + `d3-sample:latest`. **Result:** success (exit 0).

## 8. Execution Evidence
| Command | Exit | Output (summary) |
|---|---|---|
| `ruff check . && ruff format --check .` | 0 | All checks passed; 6 files formatted |
| `pytest tests/test_unit.py` | 0 | 3 passed |
| `pytest tests/test_integration.py` | 0 | 2 passed |
| `compileall app` + zip + artifact | 0 | `d3-app-6c92fc9.zip` |
| `docker build -t d3-sample:<sha>` | 0 | `sha256:c180ff50…` (16s cold / 1s cached) |
| failure run (broken unit test) | 1 | failed at stage 2, stages 3–5 skipped |
| fixed run | 0 | all 5 stages green |

---

## 9. Known Limitations
* **Local `act` + corporate proxy:** `setup-python` can't download Python inside the act runner
  container (untrusted corporate CA); evidence is captured via the command-level local runner instead.
  Real GitHub-hosted runners are unaffected. (`gh` CLI was not authenticated, so hosted-run logs
  weren't fetched programmatically; the workflow is pushed and triggers on push/PR.)
* **Docker layer cache `type=gha`** only takes effect on GitHub Actions; local proof uses the daemon's
  layer cache.
* Sample app is intentionally small (a calc + 2 endpoints) to keep the pipeline fast and the demo focused.

## 10. Agent Generated vs Verified
### Agent Generated
Workflow (`ci.yml`), cache strategy, lockfile/dependency strategy, the sample app + Dockerfile, the
local runner script, README, and this document.

### Verified (executed, evidence above)
* **Pipeline Logs:** green run, all 5 stages (§6).
* **Failure Logs:** broken unit test → exit 1, fail-fast, downstream skipped (§5).
* **Success Logs:** fixed → all stages pass (§6).
* **Container Build Logs:** `docker build` → image sha (§7).
* **Cache Evidence:** docker layer cache 16s → 1s (§4).

---

## Deliverables Checklist
- [x] Workflow YAML (`.github/workflows/ci.yml`)
- [x] Push Trigger · [x] Pull Request Trigger (+ workflow_dispatch)
- [x] Lint Stage · [x] Unit Test Stage · [x] Integration Test Stage · [x] Build Stage · [x] Container Build Stage
- [x] Dependency Cache (pip + docker gha) · [x] Lockfile Enforcement (pinned reqs)
- [x] Failure Demonstration (exit 1, stage 2, fail-fast) · [x] Success Demonstration (all green)
- [x] Logs · [x] README · [x] D3_ci_pipeline_record.md


## Screenshots

**add endpoint json**

![add endpoint json](../../screenshots/add-endpoint-json.png)

**service swagger docs**

![service swagger docs](../../screenshots/service-swagger-docs.png)

