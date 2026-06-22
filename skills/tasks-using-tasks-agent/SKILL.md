---
name: tasks-using-tasks-agent
description: >-
  Entry point for Tasks Agent skills (Base B1-B6, Intermediate I1-I6, Advanced A1-A6, DevOps D1-D6).
  Use when starting repo analysis, greenfield builds, polyglot systems, bug diagnosis,
  adversarial review, IaC / CI / Kubernetes / observability / dev-env work, or any tasks-* workflow.
  Routes to the correct specialized skill.
disable-model-invocation: false
---

# Tasks Agent

A **tiered agentic skill library** for repository understanding, safe changes, greenfield builds, advanced multi-agent orchestration, and DevOps/infra hardening. Skills are namespaced `tasks-*` and installed globally in Cursor.

## Constitution (applies to ALL tasks-* skills)

1. **Evidence-first** — every structural claim cites `file:line` or command output.
2. **Label findings** — `VERIFIED` (read/ran), `INFERRED` (convention), or `NOT FOUND IN REPOSITORY`.
3. **No guessing** — never invent endpoints, tables, or test results.
4. **Prove execution** — test/build/run claims require real terminal output.
5. **Minimal scope** — touch only what the task requires; surgical diffs for changes.
6. **Separate agent vs verified** — distinguish what was read vs what was executed.
7. **Offline-reproducible (DevOps tier)** — infra/CI/k8s artifacts must validate and prove out from a
   clone with no live cloud account (mock creds, offline plan, kind, simulated fresh clone); a check
   a reviewer can't reproduce doesn't count.

## Optional MCP boost

If `user-codegraph` MCP is connected, prefer it for symbol search, references, and call graphs. Fall back to Read/Grep/Glob — never halt if unavailable.

## Skill Router

| User intent | Load skill |
|---|---|
| Inventory repo / architecture / onboarding | `tasks-repo-inventory` |
| API map / routes / endpoints | `tasks-api-mapping` |
| Tests / CI / coverage / how to run tests | `tasks-test-discovery` |
| Build FastAPI / Python REST service | `tasks-build-fastapi-service` |
| Build Express / Node REST service | `tasks-build-node-service` |
| Build Rust CLI | `tasks-build-rust-cli` |
| ER diagram / data model / schema | `tasks-er-diagram` |
| End-to-end flow trace | `tasks-flow-trace` |
| Small safe change / minimal bug fix | `tasks-safe-change` |
| FastAPI + Node client pair | `tasks-build-polyglot-pair` |
| Dockerize / containerize service | `tasks-dockerize-service` |
| Reproduce / diagnose / fix bug | `tasks-bug-diagnosis` |
| Parallel repo analysis (6 lanes) | `tasks-parallel-repo-analysis` |
| Parallel full-stack app build | `tasks-parallel-app-build` |
| Polyglot system (FastAPI + Node + Rust) | `tasks-build-polyglot-system` |
| Modernization / Makefile / DX audit | `tasks-modernization-plan` |
| Adversarial / security review | `tasks-adversarial-review` |
| Performance profile / optimize endpoint | `tasks-performance-optimization` |
| Terraform / AWS Lambda+APIGW+S3 / IaC / `terraform plan` | `tasks-terraform-aws-stack` |
| docker-compose multi-service stack / API+DB+worker / clean re-up | `tasks-docker-compose-stack` |
| CI pipeline / GitHub Actions / coverage gate / non-root image | `tasks-ci-pipeline` |
| Kubernetes manifests / kustomize / NetworkPolicy/PDB/HPA / kind | `tasks-kubernetes-manifests` |
| Reproducible dev env / fresh-clone bootstrap / pinned toolchain | `tasks-reproducible-dev-env` |
| Observability / Prometheus / Grafana / metrics / tracing / alerts | `tasks-observability` |

## Tiers

| Tier | Skills | Focus |
|---|---|---|
| **Base (B1–B6)** | repo-inventory, api-mapping, test-discovery, build-fastapi/node/rust | Read repos + greenfield builders |
| **Intermediate (I1–I6)** | er-diagram, flow-trace, safe-change, build-polyglot-pair, dockerize, bug-diagnosis | Deeper analysis + integration |
| **Advanced (A1–A6)** | parallel-repo-analysis, parallel-app-build, build-polyglot-system, modernization-plan, adversarial-review, performance-optimization | Multi-agent orchestration + hardening |
| **DevOps (D1–D6)** | terraform-aws-stack, docker-compose-stack, ci-pipeline, kubernetes-manifests, reproducible-dev-env, observability | Offline-reproducible infra, CI, k8s, dev-env, observability |

## How to invoke

In Cursor Agent chat, type `/tasks` to search skills, or say:

```
Use tasks-repo-inventory on /path/to/repo (standard depth)
Use tasks-adversarial-review on fastapi-service/
Use tasks-using-tasks-agent — I need to dockerize a FastAPI app
```

## Source of truth

Canonical skill files live in the Tasks repo:

```text
Tasks/skills/tasks-*/SKILL.md
```

Original agent specs remain at `Basics/B*_agent.md`, `Intermediate/I*_agent.md`, `Advanced/A*/docs/`, and the hardened DevOps tasks at `DevOps-Infra/*/` (validated end-to-end in `DevOps-Infra/D_DEVOPS_VALIDATION_SUMMARY.md`).

## Install

```bash
cd /path/to/Tasks && bash scripts/install-cursor-skills.sh
```

Then **Developer: Reload Window** in Cursor.
