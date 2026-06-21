# I1 — Verification Run Results

> **Status: ✅ VERIFIED.** Every block below is real, executed output captured on the date shown.
> Environment: macOS (Darwin 25.5.0) · Python 3.14.6 · pytest 9.1.1 · run date 2026-06-21.
> Reproduce from repo root with `make i1-verify`, or from this folder per the commands below.

---

## Summary

| Check | Command | Result |
|---|---|---|
| Unit + integration tests | `python -m pytest -v` | **19 passed** in 0.04s |
| Artifact validator (offline) | `python scripts/validate_er_diagram.py` | **VALIDATION PASSED** (rc=0) |
| Artifact validator (live v19) | `… --schema-json …/EquityDatabase/19.json` | **VALIDATION PASSED** (rc=0) |
| Prisma generalizability (W19) | `… --stack prisma --prisma …/schema.prisma` | **VALIDATION PASSED** — 1 FK (rc=0) |
| Spec-sync guard | `bash scripts/check_spec_sync.sh` | **in sync** (rc=0) |
| Entity reconciliation | inventory = PK = Mermaid = appendix = 24+3 | **27 = 27 PASS** |
| Foreign keys | `grep -rn '@ForeignKey\|ForeignKey('` | **0 matches** (NOT FOUND confirmed) |

---

## 1. Tests — `pytest`

```text
$ cd Intermediate/er-diagram && python -m pytest -v
============================= test session starts ==============================
platform darwin -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: .../Intermediate/er-diagram
configfile: pytest.ini
testpaths: tests
collecting ... collected 19 items

tests/test_validate_er_diagram.py::test_happy_path_current_artifact_passes PASSED [  5%]
tests/test_validate_er_diagram.py::test_cli_offline_exit_zero PASSED     [ 10%]
tests/test_validate_er_diagram.py::test_inventory_has_27_entities PASSED [ 15%]
tests/test_validate_er_diagram.py::test_mermaid_has_27_entities PASSED   [ 21%]
tests/test_validate_er_diagram.py::test_pk_and_appendix_counts PASSED    [ 26%]
tests/test_validate_er_diagram.py::test_missing_entity_in_inventory_fails PASSED [ 31%]
tests/test_validate_er_diagram.py::test_count_mismatch_fails PASSED      [ 36%]
tests/test_validate_er_diagram.py::test_missing_mermaid_block_fails PASSED [ 42%]
tests/test_validate_er_diagram.py::test_invalid_mermaid_too_few_entities_fails PASSED [ 47%]
tests/test_validate_er_diagram.py::test_truncated_path_detected PASSED   [ 52%]
tests/test_validate_er_diagram.py::test_current_artifact_has_no_truncated_paths PASSED [ 57%]
tests/test_validate_er_diagram.py::test_missing_required_section_fails PASSED [ 63%]
tests/test_validate_er_diagram.py::test_reconciliation_all_sources_agree PASSED [ 68%]
tests/test_validate_er_diagram.py::test_required_sections_all_present_in_artifact PASSED [ 73%]
tests/test_validate_er_diagram.py::test_parse_room_schema_mini_fixture PASSED [ 78%]
tests/test_validate_er_diagram.py::test_live_schema_cross_check_reports_undocumented PASSED [ 84%]
tests/test_validate_er_diagram.py::test_prisma_detects_exactly_one_fk PASSED [ 89%]
tests/test_validate_er_diagram.py::test_prisma_fk_matches_expected_json PASSED [ 94%]
tests/test_validate_er_diagram.py::test_prisma_cli_exit_zero PASSED      [100%]

============================== 19 passed in 0.04s ==============================
```

**Result: 19 passed, 0 failed.**

---

## 2. Validator — offline (internal consistency, no repo required)

```text
$ python scripts/validate_er_diagram.py
I1 ER-diagram validator  ·  artifact: docs/agent-analysis/I1_er_diagram.md
mode: OFFLINE (internal consistency)

  [PASS] Inventory has 27 entities — found 27
  [PASS] Primary-key table has 27 rows — found 27
  [PASS] Mermaid erDiagram block present
  [PASS] Mermaid renders >= 27 entities — found 27
  [PASS] Appendix lists 27 entities — found 27
  [PASS] Reconciliation: inventory == PK == Mermaid == appendix == expected — {'inventory': 27, 'primary_keys': 27, 'mermaid': 27, 'appendix': 27} vs expected 27
  [PASS] EquityDatabase entities == 24 — found 24
  [PASS] LoggingDataBase entities == 3 — found 3
  [PASS] Per-DB split sums to total (24+3) — 24+3=27
  [PASS] Every inventory table appears in the Mermaid diagram
  [PASS] No truncated `schemas/.../` paths in evidence
  [PASS] Required sections present (Reconciliation / Agent-vs-Verified / Self-Consistency / Uncertainties)

VALIDATION PASSED
$ echo $?
0
```

---

## 3. Validator — live cross-check against the real Room export (`EquityDatabase` v19)

```text
$ python scripts/validate_er_diagram.py \
    --schema-json .../common-database/schemas/com.paytmmoney.equity_database.EquityDatabase/19.json
I1 ER-diagram validator  ·  artifact: docs/agent-analysis/I1_er_diagram.md
mode: LIVE (schema cross-check)

  ... (all offline checks PASS) ...
  [PASS] Live schema v19: all 24 tables documented in artifact
  [PASS] Live schema declares 0 foreign keys (matches artifact NOT FOUND claim) — schema fk_count=0

VALIDATION PASSED
$ echo $?
0
```

The artifact's table set and the **0-FK** claim are confirmed directly against the migrated schema JSON.

---

## 4. Validator — Prisma generalizability (W19)

```text
$ python scripts/validate_er_diagram.py --stack prisma --prisma tests/fixtures/prisma-sample/schema.prisma
I1 ER-diagram validator — Prisma stack

  [PASS] Prisma schema parsed: 3 model(s) ['User', 'Post', 'Tag']
  [PASS] Prisma @relation VERIFIED FK count == 1 — detected 1

VALIDATION PASSED
$ echo $?
0
```

Proves the validator generalizes beyond Room: it parses `schema.prisma`, recognizes `Post.author @relation(fields: [authorId], …)` as the single **VERIFIED** foreign key, and matches the fixture's `expected_fk_count.json` (`verified_fks: 1`).

---

## 5. Spec-sync guard

```text
$ bash scripts/check_spec_sync.sh
✅ check_spec_sync: I1_agent.md body is in sync with skills/tasks-er-diagram/SKILL.md
$ echo $?
0
```

---

## 6. Source-of-truth evidence (greps over `android-monorepo`)

Run from `android-monorepo/android-monorepo/`:

```text
FK grep   (@ForeignKey | ForeignKey()        -> 0 matches      [NOT FOUND confirmed]
@Entity   (common-database / equity_database) -> 24 classes
@Entity   (api_failure_logging)               -> 3 classes
@Embedded (@Embedded | Embedded()            -> 0 matches      [NOT FOUND]
@TypeConverter                                -> 11 matches     [FOUND -> §3.1]
@Dao      (common-database)                   -> 24 interfaces
@Dao      (api_failure_logging)               -> 3 interfaces
schema JSON tables  EquityDatabase v19        -> 24 tables
schema JSON tables  LoggingDataBase v7        -> 3 tables
```

**Reconciliation:** 24 (`@Entity`) = 24 (`@Database` registration) = 24 (v19 JSON), and 3 = 3 = 3 for logging → **24 + 3 = 27, PASS.** Every count the agent reported is independently reproduced above.

---

## 7. Per-entity verification checklist (27/27)

`I` = in §1 Inventory · `PK` = in §2 Primary Keys · `M` = rendered in §4 Mermaid · `A` = in Appendix A · `Reg` = in §1.1 `@Database` registration · `DAO` = in §10.

| # | Entity | Table | DB | I | PK | M | A | Reg | DAO | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | PopularSearch | `popular_search` | equity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| 2 | MostInvestedStock | `most_invested_stocks` | equity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| 3 | RecentSearch | `recent_search` | equity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| 4 | EquityConfig | `equity_config` | equity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| 5 | PersonalDetails | `personal_details` | equity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| 6 | RecentlyViewed | `recently_viewed` | equity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| 7 | HomeShortCut | `home_shortcut` | equity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| 8 | SleekCardDetails | `sleek_card_details` | equity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| 9 | AdvancedChartTypes | `advanced_chart_types` | equity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| 10 | ChartTypes | `chart_types` | equity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| 11 | YAxisScale | `y_axis_scale` | equity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| 12 | Indicators | `indicators` | equity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| 13 | TimeIntervals | `time_intervals` | equity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| 14 | FnoRanges | `fno_ranges` | equity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| 15 | EquityRanges | `equity_ranges` | equity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| 16 | PortfolioEntity | `portfolio_details` | equity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| 17 | CommonEntity | `common_details` | equity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| 18 | EquityRealisedDetail | `equity_realised_detail` | equity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| 19 | EquityRealisedSummary | `equity_realised_summary` | equity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| 20 | FnoRealisedDetail | `fno_realised_detail` | equity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| 21 | FnoRealisedSummary | `fno_realised_summary` | equity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| 22 | NotificationEntity | `pml_notification` | equity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| 23 | MtfScrips | `mtf_scrips` | equity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| 24 | KycStatusEntity | `kyc_status_data` | equity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| 25 | ApiFailureLog | `api_failure_logging` | logging | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| 26 | ApiResponseTimeLog | `api_response_time` | logging | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |
| 27 | WhiteListURLDBObj | `whitelist_url_tab` | logging | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PASS |

**27 / 27 entities verified present in all six artifact views. 0 FAIL.**

---

**Verdict: I1 is reproducible, CI-gated, and internally + externally consistent. ✅**
