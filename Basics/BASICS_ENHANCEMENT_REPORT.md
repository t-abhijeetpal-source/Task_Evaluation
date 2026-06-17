# Basics (B1–B6) — Enhancement Report (folding in `repo-reader`)

> Compared our B1–B6 agents against the reference Skill at `~/Downloads/repo-reader`, filled the
> gaps, enhanced the agents, and **ran the enhanced B1 against a local repo** (`pml-flutter`) with
> spot-validation. Date: 2026-06-17.

---

## 1. What `repo-reader` had that our B-series lacked

`repo-reader` is a single, unified, advanced repo-understanding Skill (SKILL.md +
architecture-reference.md + report-template.md + examples.md). Capabilities missing from our B-series:

| Capability | Was in B-series? | Folded into |
|---|---|---|
| Architecture pattern recognition (MVVM/Clean/MVI/BLoC/layered/event-driven) + confidence | ❌ | **B1** |
| Layer-violation detection (e.g. UI→DAO direct import) | ❌ | **B1** |
| Module dependency graph (Mermaid `graph TD` from build/imports) | ❌ | **B1** |
| Design-pattern table (Repository/Factory/DI/Mapper/Facade/UseCase…) | ❌ | **B1** |
| Static analysis (hotspots, dead-code candidates, orphaned surface, tech-debt) | partial (B2 dead routes) | **B1** + **B2** |
| Onboarding guide (day-1 read, run, debug, safest first change, ownership) | thin ("New Engineer Summary") | **B1** |
| Code-review cheat sheet | ❌ | **B1** |
| Depth modes (quick/standard/full/onboarding/code-review) | ❌ | **B1** |
| codegraph MCP discovery boost (symbols/refs/call-graph) + Grep fallback | ❌ | **B1, B2, B3** |
| Confidence & verification matrix (per-section) | ❌ | **B1, B2** |
| AI/RAG index-target notes | ❌ | **B1** (optional) |

Things our B-series already did **as well or better** (kept): per-task focus and rigor, exact
artifact paths, `VERIFIED`/`INFERRED` + `NOT FOUND IN REPOSITORY`, B2's deep auth/validation/error
flows, B3's CI-command-is-canonical + Agent-vs-Verified split, B4/B5/B6 actually built & tested.

---

## 2. Enhancements applied

- **`B1/B1_agent.md` — rewritten to v2 (repo-reader grade).** Added depth modes, codegraph-first
  discovery table, architecture analysis + layer map + violations, module dependency graph,
  design-pattern table, static-analysis phase, onboarding guide + code-review cheat sheet,
  confidence matrix, and a 16-section report format — while preserving B1's required inventory
  sections and verification rules.
- **`B2/B2_agent.md` — v2 additions appended.** codegraph boost; unused/orphaned-route detection
  via `find_references` (tagged *candidate*); confidence matrix; client-repo reminder (outbound
  surface + frontend routes).
- **`B3/B3_agent.md` — v2 additions appended.** CI-command-canonical + coverage-gate + stale-doc
  detection (reinforced); narrowest-safe-command-first; **self-validate example paths** (a missing
  example path is a hard defect); Agent-vs-Verified split reinforced.
- **B4/B5/B6** — these are *builders*, not readers; `repo-reader` doesn't map onto them. Left as-is
  (already built, tested, and verified).

---

## 3. Ran enhanced B1 against a local repo — `pml-flutter`

**Command:** enhanced B1 (default depth) executed against
`android-monorepo/flutter/pml-flutter`. **Artifact:**
`Basics/repo-structure-mapper/B1_repo_inventory_pml-flutter.md` (34 KB).

**Findings (highlights):**
- 18 feature modules; ~63 ViewModels; ~104 repository files (abstract in `domain/`, impl in `data/`);
  ~100 use cases; ~136 models; ~46 registered nav routes across 21 route files.
- **Architecture verdict:** feature-first **Clean Architecture + MVVM with Riverpod** (state + DI) +
  `go_router`, inside a **FlutterBoost-style native container** (`PMLStackCore`) with a Pigeon
  native bridge. Client app — no server endpoints, no Flutter-side DB.

**Spot-validation of headline claims (I re-checked against source):**
| Claim | Verified? | Evidence |
|---|---|---|
| Layer violation: presentation imports data layer directly | ✅ | `lib/features/expert_picks/presentation/expert_picks_list_view_model.dart:5,7` import `pml_bridge_repository_impl.dart` + `expert_picks_remote_datasource.dart` |
| HTTP layer is `package:http`, not Dio (README drift) | ✅ | `pubspec.yaml:35` `http: ^1.4.0`; no `dio:` dependency |
| 4 environments | ✅ | `lib/core/network/api_environment.dart:4-8` enum `production, staging, dev, preProd` |

The new B1 demonstrably surfaces things the old inventory format would have missed — a real layer
violation (cited), documentation drift (README vs code), and a dead-dependency candidate
(`socket_io_client` declared but `web_socket_channel` active).

---

## 4. Open items

- The original `B1/B1_repo_inventory.md` (target: external `chai-backend`) is retained for
  reference; the new local-repo artifact is `B1_repo_inventory_pml-flutter.md`.
- Counts in the pml-flutter run are naming-sweep `INFERRED` (not enumerated 1:1) — flagged in the
  artifact's confidence matrix.
- The same enhanced B1 can be run against **paytmmoney / android-monorepo** (Android Kotlin
  multi-module) to showcase the module dependency graph + Hilt DI + Room data model — a natural
  next run.
