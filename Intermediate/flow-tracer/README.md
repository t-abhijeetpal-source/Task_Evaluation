# I2 — Flow Tracer

End-to-end trace of one (now **two**) business flow(s) in the `android-monorepo` super-repo, from UI trigger to final side effect, with every hop cited at `file:line` and **reproducibly verifiable** against a pinned commit.

| | |
|---|---|
| **Primary flow (A)** | **Add security to watchlist** — watchlist icon tap → `POST /marketwatch/api/v1/watchlist/{id}/security` → native cache `sync()` (Retrofit `GET`). **33 hops, all VERIFIED.** |
| **Secondary flow (B)** | **Recent-search persistence** — search/bookmark → parallel `PUT` event API **+** Room write to `recent_search`. Re-verified here; full trace in A1. |
| **Pinned commit** | `e7fc70a6b564ca3baffecb9a652194702443df3b` (2026-06-20, branch `bugfix/PM4-6240-scheme-holding-tab-inaccessible-initially`) |
| **Target repo** | `android-monorepo` (read-only; not vendored into this Tasks repo) |

## Deliverables

| File | What it is |
|---|---|
| `docs/agent-analysis/I2_flow_trace.md` | The trace: entry point, 33-hop path, DI bindings, auth-header chain, side effects, dependency + sequence + **error-path** diagrams, known uncertainties, self-consistency check. |
| `I2_callgraph.yaml` | Machine-readable call graph: nodes (`file:line:fn:confidence`), DI bindings, side effects, error paths, auth headers — for both flows. |
| `scripts/verify_trace.sh` | Asserts all 36 load-bearing edges exist at the pinned commit. Exit 0 = green. |
| `I2_verification_report.md` | Independent **blind adversarial** verification (10/10 claims confirmed) + corroboration & uncertainty ledger. |
| `I2_agent.md` | Execution plan + orchestration log (5 evidence agents + 1 adversarial verifier). |

## Reproduce

The target repo is external and read-only. To replay this trace against the exact source it was built from:

```bash
# 1. Point the verifier at your android-monorepo git root and pin the commit.
#    (Default path is the local clone; override via arg or $ANDROID_MONOREPO.)
export ANDROID_MONOREPO=/path/to/android-monorepo        # the git root
git -C "$ANDROID_MONOREPO" checkout e7fc70a6b564ca3baffecb9a652194702443df3b

# 2. Run the verifier — asserts every cited file:line still says what the trace claims.
bash scripts/verify_trace.sh                 # or: bash scripts/verify_trace.sh "$ANDROID_MONOREPO"
```

Expected output ends with:

```
Result: 36 pass, 0 near (drift), 0 fail  / 36 total
All trace edges verified.
```

- If HEAD ≠ the pinned commit, the script **warns** and still runs; edges that moved are reported as `~near` (drift, non-fatal within ±8 lines) or `FAIL` (genuinely gone).
- Exit code is `0` only when there are **0 failures**, so the script is CI-gateable.

## How this trace was produced

Depth-first from the entry point, one hop at a time, resolving each DI/provider/bridge edge to its concrete implementation before moving on (per the `tasks-flow-trace` skill). Evidence was gathered by 5 parallel sub-agents (each returning `file:line` + quoted source), then **independently re-verified by a 6th agent blind to the derivation**. See `I2_agent.md` for the orchestration log and `I2_verification_report.md` for the adversarial pass.

## Note on the previous version

The earlier artifact traced the watchlist-add flow with approximate `~line` numbers, 7 INFERRED hops, and no scripts. This version: exact line numbers at a pinned commit, **0 INFERRED hops on the happy path** (the `sendNativeData`, bridge-default, `handleDeeplink`, and native-`sync()` gaps are now resolved), a native-sync sub-trace to the Retrofit boundary, full DI + auth-header appendices, the recent-search flow reconciled as Flow B, an error-path diagram, a machine-readable graph, and a CI-gateable verifier.
