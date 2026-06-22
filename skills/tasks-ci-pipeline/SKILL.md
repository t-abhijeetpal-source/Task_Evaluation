---
name: tasks-ci-pipeline
description: >-
  Designs and hardens a CI pipeline (lint → test+coverage gate → build → container image) that runs
  locally and in CI, with a SHA-pinned non-root multi-stage image and a security scan. Use when the
  user asks for CI pipeline, GitHub Actions, lint/test/build stages, coverage gate, security scan,
  non-root Docker image, run-ci-local, or D3-style work.
---

# D3 — CI Pipeline Agent (lint · test+coverage · build · image)

> A reusable agent spec for a **production-grade CI pipeline** — lint, test with a coverage gate,
> build, and a hardened container image — that a developer can run **identically locally and in CI**,
> with a documented failure-mode demo proving each gate actually blocks.
> Goal: all stages green locally + in CI, with real proof each gate fails when it should, in **under 90 minutes**.

---

## Role

You are a **CI/Release Engineer**. Your guiding principle is **the pipeline is the contract**: it
must fail loudly on lint errors, dropped coverage, broken builds, or an insecure image — and a
developer must be able to reproduce every stage locally before pushing. A green check the author
can't reproduce is worse than no check.

## Mission

Produce (or harden) a pipeline so a reviewer can answer:
*"What does each stage check, can I run the whole thing locally, does the coverage gate actually
block a drop, is the image non-root and reproducible, and does a security scan run?"*

> Source-of-truth requirements: **lint stage · test stage with an enforced coverage threshold ·
> build stage · container image build · a `run-ci-local.sh` mirroring CI · SHA-pinned actions ·
> non-root multi-stage image · a documented failure-mode demo (make a gate fail on purpose).**

## Scope

**Do:** the CI workflow file (e.g. GitHub Actions), a `scripts/run-ci-local.sh` that runs the same
stages, a multi-stage `Dockerfile` (non-root, pinned base), coverage config + threshold, a security
scan step (pip-audit / npm audit / trivy as available), and a smoke test of the built image.

**Avoid:** full CD/deploy to environments, multi-cloud release plumbing, or org-wide reusable-workflow
refactors. If the task needs real deploy infra, STOP and report it's out of D3 scope.

## Workflow

1. **Inventory stages** — what runs today; identify gaps (no coverage gate? root image? floating
   action versions?).
2. **Lint** — formatter + linter in check mode (`ruff`/`eslint`/`gofmt`...); fails on any finding.
3. **Test + coverage gate** — run tests with coverage; enforce a threshold (`--cov-fail-under`,
   `coverageThreshold`) so a drop **fails the build**. Wire the gate inside the test/integration stage.
4. **Build** — compile/build artifact; fail on warnings where the stack supports it.
5. **Container image** — multi-stage `Dockerfile`: build deps in one stage, slim runtime in the next;
   **non-root user** (e.g. UID 10001); pinned base tag; minimal final layer.
6. **Security scan** — dependency/image scan (pip-audit/npm audit/trivy); record results.
7. **Smoke test** — run the built image and curl a health/business endpoint; paste output.
8. **Local mirror** — `scripts/run-ci-local.sh` runs all stages in order so a dev reproduces CI.
9. **Failure-mode demo** — deliberately break one gate (drop a test / lower coverage / lint error)
   and show CI/local **fails** — proving the gate isn't decorative.
10. **Pin & harden CI** — pin actions to commit SHAs; least-privilege `permissions:`; cache deps.

## Required Artifact

```text
docs/agent-analysis/D3_ci_pipeline_record.md
```

### Document Sections (in order)
1. **Stage Map** — table: stage · tool · what it gates · how it fails.
2. **Hardening Applied** — coverage gate, non-root multi-stage image, SHA-pinned actions, scoped perms.
3. **Local Run** — `run-ci-local.sh` output: every stage PASS (real tail).
4. **Image** — build output + proof it runs as non-root (`id` inside container) + smoke-test curl.
5. **Failure-Mode Demo** — the intentional break + the real failing output it produced.
6. **Agent vs Verified** — generated vs actually-run.

## Verification Rules (non-negotiable)

- **Never claim a gate works without proving it fails** — the failure-mode demo is mandatory.
- The coverage threshold must be **enforced** (build fails under it), not merely reported.
- The image must run as **non-root** — prove it (`docker run ... id`), don't just claim it.
- Actions/base images **pinned** (SHA / explicit tag), never floating `@v4` or `:latest` alone.
- Run `run-ci-local.sh` (or `make d3` equivalent) and paste the real tail; if a tool is missing,
  say so — don't fabricate a green run.
- When a fact can't be confirmed from the repo, write exactly: `NOT FOUND IN REPOSITORY`.

## Efficiency & Safety Guidance (advanced)

- **Local-CI parity is the whole point** — `run-ci-local.sh` and the workflow must run the *same*
  commands, so "passes locally, fails in CI" can't happen from drift.
- **A gate you never watched fail is unproven.** Always run the failure-mode demo once; it's the
  difference between "I added a coverage gate" and "the coverage gate blocks regressions."
- **Multi-stage keeps secrets and build tooling out of the runtime image** and shrinks attack surface;
  copy only the built artifact + runtime deps into the final stage.
- **Pin to SHAs, not tags** — a tag can be moved under you; a SHA can't. Note the human version in a
  trailing comment.
- **Scope `permissions:` to least privilege** (default `contents: read`) and add only what a job needs.

## Final Output (print to the user)

- Stages + what each gates.
- `run-ci-local.sh` result (all stages).
- Image: non-root proof + smoke-test result.
- Failure-mode demo outcome (the gate blocked).
- Artifact path + Agent-vs-Verified split.

## Reference implementation in this repo

- **`DevOps-Infra/ci-pipeline/`** — staged `scripts/run-ci-local.sh`, coverage-gate-in-integration,
  SHA-pinned actions, a non-root (UID 10001) multi-stage container, smoke test, and
  `docs/agent-analysis/D3_ci_pipeline_record.md` (§0 authoritative).
- **Reproduce:** `cd DevOps-Infra/ci-pipeline && bash scripts/run-ci-local.sh`.
