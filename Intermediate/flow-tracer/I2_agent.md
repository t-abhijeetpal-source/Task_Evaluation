# I2 — Execution Plan & Orchestration Log

> This file is **not** a copy of the agent spec. The reusable spec lives in the skill
> `skills/tasks-flow-trace/SKILL.md`. This is the **execution record** for the I2 trace of
> `android-monorepo` @ `e7fc70a6b564ca3baffecb9a652194702443df3b` — what was planned, how the work
> was decomposed across agents, and what each returned.

---

## Objective

Trace the **add-to-watchlist** flow (Flutter UI → backend POST → native cache sync) end-to-end with
exact `file:line` evidence at a pinned commit, resolve all previously-INFERRED hops to VERIFIED,
add a second corroborating flow (recent-search), and make the whole thing reproducibly verifiable.

## Plan

1. **Pin & orient.** Confirm the repo, capture the HEAD SHA, locate the real file paths (several
   had moved vs the old artifact, e.g. `PMLWatchlistViewModel` lives under `company_page/`, not a
   `watchlist/` feature).
2. **Decompose into independent, non-overlapping evidence tasks** and fan out (depth-first within
   each segment; resolve each DI/bridge edge to its concrete impl before moving on).
3. **Synthesize** verified edges into the trace doc + machine-readable graph + verifier script.
4. **Adversarially verify** with an agent blind to the derivation.
5. **Reconcile** docs (fix the stale "recent-search" README claim) and self-score.

## Orchestration log

### Phase 0 — Prerequisites (coordinator, inline)
- Target repo confirmed. The git root is the **nested** `android-monorepo/android-monorepo`
  (outer dir is not a repo). Pinned `HEAD = e7fc70a6b564ca3baffecb9a652194702443df3b`
  (2026-06-20, branch `bugfix/PM4-6240-...`).
- Read baseline: old `I2_flow_trace.md`, the skill, the gold-standard `A1_flow_trace.md` +
  `A1_verification_report.md`, `Intermediate/VALIDATION_REPORT.md`, and `Tasks/README.md:130`
  (the stale claim).
- Verified key entry files exist; corrected paths for the bottom sheet / viewmodel.

### Phase 1 — Evidence fan-out (5 parallel sub-agents)
| Agent | Scope | Result |
|---|---|---|
| 1 | Flow A UI→POST (hops 1-19) + resolve `_useBridge` default | All 19 verified; `_useBridge=false` @ `api_manager.dart:33`; documented the param double-swap |
| 2 | Post-success + native sync entry (hops 20-26) | Resolved `sendNativeData` → `PMLSendDetailsDataUseCase` (bridge `getNativeData`) and `handleDeeplink` → `PMLBridgeName.handleDeepLink`; confirmed only equity_sdk handles `sync_watchlist` |
| 3 | Native `sync()` sub-trace → Retrofit/Room | 7 hops to terminal Retrofit `@GET`; **no Room write** (in-memory LiveData); Dagger bindings in `CommonEquityWatchlistModule` |
| 4 | Riverpod DI table + auth-header chain | 9 providers mapped; header injection traced app-init → native bridges → `HttpApiClient._globalHeaders` → request; base URL literal confirmed |
| 5 | Flow B (recent-search) re-verification @ pin | Whole A1 chain intact; line drift folded in (Fragment +7, VM +53); PUT+Room fan-out confirmed |

### Phase 2 — Synthesis (coordinator, inline)
- Coordinator personally read the error-path handlers (`api_manager.dart:121-155`,
  `PMLWatchlistViewModel.dart` catch blocks, `PMLCompanyPage.dart:806-855`) to source the
  error-path diagram first-hand rather than trusting the happy-path agents.
- Authored: `docs/agent-analysis/I2_flow_trace.md`, `I2_callgraph.yaml`, `scripts/verify_trace.sh`.

### Phase 3 — Verification
- **3a Automated:** `verify_trace.sh` → 36/36 edges pass at the pinned commit (exit 0).
- **3b Blind adversarial:** a 6th agent, given only claims, returned **10 CONFIRMED / 0 REFUTED**
  and surfaced one extra fact (`removeFromWatchlist` shares the param swap). See
  `I2_verification_report.md`.

### Phase 4 — Reconciliation
- Fixed `Tasks/README.md:130`: the portfolio entry named only "recent-search flow"; updated to name
  the primary watchlist-add flow with recent-search as the corroborating Flow B.
- Self-score: **97/100** (no automatic cap triggers).

## Deviations / notes
- Artifact root is `Intermediate/flow-tracer/` (a proper sibling), not `/docs` at repo root — the
  trace doc is under `docs/agent-analysis/` within this folder, matching the portfolio convention.
- Native watchlist cache is **in-memory `LiveData`**, not Room — the original artifact's "cache
  refresh" wording was correct but is now made explicit to avoid implying a DB write.
