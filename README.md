# Task_Eval — Coding-Agent Capability Portfolio

A graded, end-to-end portfolio demonstrating what a coding agent can do across the full software
lifecycle — **understand, build, verify, harden, optimize, and operate** real systems in
**Python, Node.js, Rust, Terraform, Docker, and CI/CD**.

Every task was executed for real and **verified with captured evidence** (tests run, builds passed,
containers healthy, plans clean) — never "looks done". Each task ships its own
`docs/agent-analysis/*.md` record with an explicit **Agent-Generated vs Verified** split.

> **🌐 Live platform:** **https://agent-platform-teal-three.vercel.app** — a premium AI Agent
> Marketplace & Evaluation Platform (Next.js) that browses every agent below, with prompts,
> demo outputs, metadata, copy/download, dark mode, and a ⌘K command palette.
>
> **📦 Repo:** https://github.com/t-abhijeetpal-source/Task_Eval

---

## 📚 Task tiers

| Tier | Folder | Theme | Tasks |
|---|---|---|---|
| **Basics** | `Basics/` | Read a repo · build a small service | B1–B6 |
| **Intermediate** | `Intermediate/` | Model · trace · change · integrate · containerize · debug | I1–I6 |
| **Advanced** | `Advanced/` | Multi-agent orchestration · review · perf | A1–A6 |
| **DevOps & Infra** | `DevOps-Infra/` | IaC · Compose · CI · Kubernetes · observability · reproducibility | D1–D6 |
| **Platform** | `agent-platform/` | The website that showcases all of the above (Next.js, deployed) | — |

---

### 🟢 Basics (B1–B6)
| # | Task | Demonstrates | Evidence |
|---|---|---|---|
| B1 | Repo Structure Mapper | Inventory + architecture + dependency graph of any repo | validated on android-monorepo (27 tables, 0 FKs, 0 mismatches) |
| B2 | Route & API Mapper | Endpoint/outbound-API map with auth/validation/error flows | paytmmoney: 11 Retrofit services, dynamic `@Url` confirmed |
| B3 | Test Discovery | Frameworks, layout, coverage gate, canonical CI command | found `:advisory` missing from `settings.gradle` |
| B4 | FastAPI service builder | Layered Python service + tests | `pytest` 6 passed + live curl |
| B5 | Node service builder | Layered Express service + tests | `npm test` 7 passed |
| B6 | Rust CLI builder | Deterministic CLI (lib+bin) + tests | `cargo test` 7 passed |

### 🔵 Intermediate (I1–I6)
| # | Task | Demonstrates | Evidence |
|---|---|---|---|
| I1 | ER Diagram | Data model + Mermaid ER from source, reconciled | 27 tables; no-FK cache pattern |
| I2 | E2E Flow Tracer | UI→VM→UseCase→Repo→DB trace with DI resolution | recent-search flow, file:line cited |
| I3 | Minimal Safe Change | Smallest safe change + before/after tests + rollback | pml-flutter date parser, `flutter test` 40/40 |
| I4 | Polyglot Pair | FastAPI service + Node client on one contract | pytest 7 + jest 9 + live integration |
| I5 | Dockerize | Slim, non-root, health-checked image | container Up (healthy), 55 MB |
| I6 | Bug Diagnosis | Reproduce → root-cause → fix → verify | 3 failed → fix → 5 passed |

### 🟣 Advanced (A1–A6)
| # | Task | Demonstrates | Evidence |
|---|---|---|---|
| A1 | Parallel Repo Analysis | 6 specialist agents → cross-verify → master report | independent verifier; 2 contradictions resolved |
| A2 | Parallel System Builder | 6 agents build a full-stack app, integrated | Expense Tracker: 16 tests, Docker healthy |
| A3 | Polyglot Fraud System | FastAPI + Node worker + Rust engine, one contract | rust 6 / py 10 / node 12; **E2E 4/4 PASS** |
| A4 | Repo Modernization | Value/risk matrix + execute #1 safe step | gradle `distributionSha256Sum` pin, `gradlew` verified |
| A5 | Adversarial PR Review | Assume-wrong review, reproduce findings | reproduced Critical path-traversal + auth bypass in A3 |
| A6 | Performance Optimization | Measure → profile → minimal change → prove | `/summary` 278ms → 20ms (**−92.7%**), 16/16 tests |

> A5 found 3 blocking issues in A3; A3 was then **hardened + regression-tested** (fastapi 7 → 10).

### 🟠 DevOps & Infra (D1–D6)
| # | Folder | Task | Demonstrates | Evidence |
|---|---|---|---|---|
| D1 | `terraform-aws-stack` | Terraform Plan | Pinned, validated IaC (S3 + Lambda + API GW) | `validate` 0 errors; clean plan (15 to add) |
| D2 | `docker-compose-stack` | Compose E2E Stack | API + PostgreSQL + worker, health-gated startup | build→up→seed→E2E→down, all exit 0 |
| D3 | `ci-pipeline` | CI Pipeline | 5-stage GitHub Actions + cache + fail→fix demo | fail at stage 2 → fix → all green |
| D4 | `kubernetes-manifests` | Kubernetes Manifests | Deployment/Service/probes, validated on a local cluster | manifests applied + verified |
| D5 | `reproducible-dev-env` | Reproducible Dev Env | One-command `make bootstrap` (mise-pinned runtimes) | clean-slate **85/85 tests green** |
| D6 | `observability-bolt-on` | Observability | Structured logs + Prometheus metrics + health/readiness | scrape + probes verified (Prometheus/Grafana) |

---

## 🗂 Repository structure
Folders are named for what they do (no cryptic codes):
```
Task_Eval/
├── Basics/                 repo-structure-mapper · route-api-mapper · test-discovery ·
│                           fastapi-transaction-service · node-transaction-service · rust-logcount-cli
├── Intermediate/           er-diagram · flow-tracer · minimal-safe-change ·
│                           polyglot-currency-pair · dockerize-service · bug-diagnosis
├── Advanced/               parallel-repo-analysis · parallel-expense-tracker · polyglot-fraud-system ·
│                           repo-modernization · adversarial-pr-review · performance-optimization
├── DevOps-Infra/           terraform-aws-stack · docker-compose-stack · ci-pipeline ·
│                           kubernetes-manifests · reproducible-dev-env · observability-bolt-on
├── agent-platform/         Next.js website (deployed to Vercel)
├── skills/                 reusable task-agent skill definitions
├── mise.toml               pinned runtimes (Python 3.12.7 · Node 22.11.0 · Rust 1.83.0)
├── .tool-versions          asdf-compatible mirror
├── .env.example            env-var template (copied to .env by `make setup-env`)
├── Makefile                single-command entrypoint (`make bootstrap`)
└── .github/workflows/      CI pipeline
```
Each task folder contains its implementation, tests, and a `docs/agent-analysis/*.md`
record with commands, raw output, and the Agent-vs-Verified split.

---

## 🚀 Getting started (reproducible — D5)
**Prerequisites:** [`mise`](https://mise.jdx.dev) + `make`. (Docker only for the container/compose tasks.)

```bash
git clone git@github.com:t-abhijeetpal-source/Task_Eval.git
cd Task_Eval
make bootstrap     # pin runtimes → install all deps → generate .env → build + test (85 tests)
make test          # re-run the full suite anytime
make help          # list all targets
```
Per-language: `make python` · `make node` · `make rust`. End-to-end demo: `make a3-integration`.

### Run the website locally
```bash
cd agent-platform
npm install
npm run dev        # http://localhost:3000   (or: npm run build && npm run start)
```

---

## 🧱 Tech stack
Python 3.12 · Node 22 · Rust 1.83 · FastAPI · Express · SQLAlchemy/SQLite · PostgreSQL · Docker &
Compose · Terraform · GitHub Actions · mise · pytest / jest / cargo test ·
Next.js 16 + React 19 + TypeScript + Tailwind v4 + Framer Motion (the platform).

## ✅ Verification at a glance
- **85 tests** pass on a clean-slate `make bootstrap` (Rust 13 · Node 28 · Python 44).
- A3 end-to-end **4/4 PASS**; A2 **16/16**; D2 stack health-gated; D1 plan clean; D3 fail→fix proven.
- Every claim is backed by captured terminal output in the per-task records.

## 📄 Records & honesty
- Per task: `docs/agent-analysis/<TASK>_*.md` (+ `VERIFICATION_RESULTS.md` where applicable).
- Consolidated: `Advanced/parallel-repo-analysis/.../A1_repository_master_report.md`, `Advanced/VALIDATION_REPORT.md`,
  `Basics/BASICS_ENHANCEMENT_REPORT.md`, `DevOps-Infra/*/docs/agent-analysis/`.
- Limitations and environment blockers (disk, corporate TLS proxy) are documented honestly where they occurred.

---

*Built and verified with Claude Code. Author: Abhijeet Pal.*
