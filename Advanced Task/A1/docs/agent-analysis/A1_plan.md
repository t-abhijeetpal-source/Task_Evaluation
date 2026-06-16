# A1 — Parallel Repository Analysis: Orchestration Plan

> Role: Principal Software Architect & Multi-Agent Coordinator.
> Objective: demonstrate **effective parallel agent orchestration** — decompose, fan out 6
> independent specialist agents, cross-verify, resolve conflicts, consolidate.
> Target repo: `/Users/abhijeetpal/Desktop/workspace/android-monorepo` (Paytm Money codebase:
> Kotlin equity SDK + Room DB + Flutter app). Date: 2026-06-17.

---

## Scope & shared constraints (apply to ALL agents)

- **Scope focus:** the equity vertical — `common-database/`, `equity_sdk/`, `base_app/`, and the
  Flutter client `flutter/pml-flutter/`. Report counts for out-of-scope modules; don't deep-read them.
- **Independence:** each agent works ALONE. **Do not read another agent's report.** No copying
  findings. (This is what makes Phase 3 cross-verification meaningful.)
- **Evidence rule:** every claim cites a real `file[:line]` and is labeled `VERIFIED` (read it),
  `INFERRED` (naming/convention), or `UNVERIFIED` (couldn't confirm). Use `NOT FOUND IN REPOSITORY`
  when absent. Never guess.
- **Output:** each agent WRITES exactly one report file (paths below). Read-only on the repo —
  no repo modifications. Use grep/glob on conventions; prefer schema artifacts and manifests.
- **Depth-cap:** cap ~15 items per group; summarize the long tail with counts + `+N more in <path>`.

---

## Task decomposition — the 6 lanes

| # | Agent | Mission | Scope | Deliverable | Verification strategy |
|---|---|---|---|---|---|
| 1 | **Repository Inventory** | Module/artifact inventory: modules, services, repositories, ViewModels, models, jobs, utils, configs | top-level modules + equity vertical | `A1_inventory.md` | cite `settings.gradle`/`build.gradle` for modules; grep naming conventions; counts per group |
| 2 | **API Mapping** | Outbound API surface (Retrofit services) + Flutter routes/HTTP | `equity_sdk`, `base_app`, `flutter/pml-flutter` | `A1_api_map.md` | grep `@GET/@POST/@Url`, OkHttp interceptors; cite interface files; mark unused via reference search |
| 3 | **Database & Entity** | Room data model: entities, tables, PKs, FKs, relationships | `common-database/` (+ `api_failure_logging`) | `A1_entities.md` | authoritative = exported `schemas/**/<maxver>.json`; reconcile vs `@Entity`/`@Database`; ER Mermaid |
| 4 | **Test Discovery** | Frameworks, test layout, coverage gate, canonical CI command | all in-scope modules | `A1_tests.md` | cite `build.gradle` deps + CI YAML (`.gitlab-ci.yml`/bitbucket); verify example test paths exist; do NOT run gradle (state blocker) |
| 5 | **Architecture & Dependency** | Pattern (Clean/MVVM/MVI/Hilt), layer map, module dependency graph, design patterns, violations | equity vertical | `A1_architecture.md` | folder/DI evidence; module graph from build files; cite a layer violation if found; Mermaid |
| 6 | **Flow Trace** | One end-to-end flow → final side effect (DB write or API call) | a search/portfolio/recent flow | `A1_flow_trace.md` | trace `file::function` per hop; resolve DI bindings; sequence diagram; tag uncertain `(inferred)` |

---

## Required report files (Phase 2)

```text
Advanced Task/A1/docs/agent-analysis/
├── A1_plan.md                     (this file — Phase 1)
├── A1_inventory.md                (Agent 1)
├── A1_api_map.md                  (Agent 2)
├── A1_entities.md                 (Agent 3)
├── A1_tests.md                    (Agent 4)
├── A1_architecture.md             (Agent 5)
├── A1_flow_trace.md               (Agent 6)
├── A1_verification_report.md      (Phase 3 — coordinator)
└── A1_repository_master_report.md (Phase 4 — coordinator)
```

---

## Merge order & conflict/risk plan

- **Merge order (Phase 4):** Inventory → Architecture → Entities → API → Flow → Tests. Rationale:
  structure first (what exists), then how it's organized, then data, then interfaces, then dynamic
  behavior, then quality gates. Later lanes are reconciled against earlier structural facts.
- **Conflict policy:** if two agents disagree (e.g. Architecture says "Clean" but Inventory shows no
  `domain/`), the coordinator re-checks source and records the resolution with evidence. The agent
  with the cited `file:line` wins; unresolved disagreements are logged as `UNVERIFIED`.
- **Risk — overlap:** API (Agent 2) and Flow (Agent 6) may both touch the network layer; Entities
  (Agent 3) and Inventory (Agent 1) may both list models. This is expected and is the *input* to
  cross-verification (dedupe + corroborate), not a failure.
- **Risk — scale:** 104-module monorepo → agents depth-cap to the equity vertical and report counts.
- **Risk — binary/generated code:** some equity/kyc services live in binary modules (only `build/`
  copies) → mark `NOT FOUND IN REPOSITORY`, don't infer.

---

## Verification plan (Phase 3)

The coordinator (not the agents) will:
1. **Contradictions** — diff overlapping claims across reports; resolve against source.
2. **Missing findings** — note what one agent found that an overlapping agent missed.
3. **Duplicates** — same finding from multiple agents → corroboration (raises confidence).
4. **Unverified assumptions** — flag any `INFERRED`/`UNVERIFIED` claims that matter.
5. **Independent spot-checks** — re-grep a sample of each agent's headline claims against source.
6. Assign each major finding a review trail: **Discovered by → Verified by → Final status**.

Output: `A1_verification_report.md`, then the consolidated `A1_repository_master_report.md`.

---

## Metrics to report (Phase 4)

Files scanned · Modules discovered · Endpoints mapped · Entities found · Tests discovered ·
Contradictions resolved.
