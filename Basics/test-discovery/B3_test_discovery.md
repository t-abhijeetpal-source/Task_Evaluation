# B3 — Test Discovery & Execution Report: pml-flutter

**Repository:** `android-monorepo/flutter/pml-flutter` (package `flutter_pml_app`)  
**Agent run date:** 2026-06-16  
**Flutter version (`.fvmrc`):** 3.35.5

---

## 1. Framework

| Item | Value | Evidence |
|------|-------|----------|
| **Primary runner** | `flutter_test` (Flutter SDK) | `pubspec.yaml` → `dev_dependencies.flutter_test: sdk: flutter` |
| **Mock library** | `mockito` ^5.6.4 | `pubspec.yaml` |
| **Code generation** | `build_runner` ^2.6.0 (for `@GenerateMocks`) | `pubspec.yaml`, `docs/testing-guide.md` |
| **Async testing** | `fake_async` ^1.3.3 | `pubspec.yaml` |
| **Lint/analysis** | `very_good_analysis` ^6.0.0 | `analysis_options.yaml` |
| **Dedicated test config** | NOT FOUND IN REPOSITORY | No `dart_test.yaml`; runner uses Flutter defaults |
| **Pinned Flutter** | 3.35.5 | `.fvmrc` |

### Agent Findings

- Unit and widget tests use the standard Flutter `test/` tree and `flutter test`.
- Mockito mocks are generated into `*_test.mocks.dart` files via `dart run build_runner build --delete-conflicting-outputs`.
- A local `core/` package also declares `flutter_test` in `core/pubspec.yaml`.
- Root-level `integration_test/` exists (10 Dart files) but **`integration_test` and `patrol` are removed from `pubspec.yaml`** in this monorepo-embedded copy (comment in `pubspec.yaml` lines 76–79). E2E is expected in the standalone repo or via native Maestro in the monorepo.

### Verified Findings

```bash
cd /Users/abhijeetpal/Desktop/workspace/android-monorepo/flutter/pml-flutter
flutter pub get
# → succeeded (also runs `cd core && flutter pub get` in CI)
```

---

## 2. Test Structure

### Directory layout

```
test/                          # 211 *_test.dart files
├── core/                      # 41 files — network, bridge, socket, utils, theme
├── features/                  # 156 files — feature modules mirror lib/features/
│   └── <feature>/
│       ├── data/
│       ├── domain/
│       ├── presentation/
│       └── integration/       # 13 in-tree “integration” tests (still run via flutter test)
├── common/                    # 7 files
├── pmlcharts/                 # 6 files
└── test_utils/                # shared builders/helpers

integration_test/              # 10 files — NOT wired in pubspec (monorepo copy)
core/test/                     # NOT FOUND IN REPOSITORY (no tests under core/ yet)
```

### Naming convention

- Source: `lib/features/<feature>/.../<name>.dart`
- Test: `test/features/<feature>/.../<name>_test.dart`
- Generated mocks: `<test_file>.mocks.dart` alongside the test

### Split (approximate)

| Layer | Count / signal | Example paths |
|-------|----------------|---------------|
| **Unit** | ~180+ files (pure logic, models, use cases, viewmodels) | `test/core/utils/date_time_utils_test.dart`, `test/features/orderpad/data/validators/orderpad_form_validator_test.dart` |
| **Widget** | ~25 files using `testWidgets(` | `test/features/flash_trade/presentation/ui/screens/flash_trade_contracts_screen_test.dart`, `test/core/socket/socket_health/widgets/socket_health_app_shell_test.dart` |
| **In-tree integration** | 13 files under `test/**/integration/` | `test/features/corporateEvents/integration/corporate_events_detail_integration_test.dart`, `test/features/past_orders/data/datasources/past_orders_integration_test.dart` |
| **E2E (`integration_test/`)** | 10 files on disk; **not runnable** from this copy without restoring `integration_test` in pubspec | `integration_test/flash_trade/flash_trade_landing_test.dart`, `integration_test/patrol/app_patrol_test.dart` |

### Agent Findings

- Tests are organized by feature, mirroring Clean Architecture layers (`data/`, `domain/`, `presentation/`).
- Strong coverage in `core/` (network, socket health, bridge) and several features (`corporateEvents`, `flash_trade`, `mtf_statement`, `research_ideas`, `pmlcharts`).
- Documented gaps: `charts`, `kyc`, parts of `TFCOptions` have incomplete or stub test files (`MATURITY_REPORT.md`).

---

## 3. Commands

All commands assume repo root and dependencies installed (`flutter pub get` + `cd core && flutter pub get`).

### Run all tests

```bash
flutter test
```

### Run one file

```bash
flutter test test/core/utils/date_time_utils_test.dart
```

### Run one test by name

```bash
flutter test --name "DateTimeUtils"
```

### Run with coverage

```bash
flutter test --coverage
# Output: coverage/lcov.info
```

### Coverage threshold check (local script — 30% default)

```bash
./scripts/check-coverage.sh
# or with custom threshold:
./scripts/check-coverage.sh 4
```

### HTML coverage report

```bash
make coverage-html   # requires lcov: brew install lcov
```

### Pre-submit check (lint + format + test)

```bash
make check
```

### Generate Mockito mocks (required before some tests compile)

```bash
dart run build_runner build --delete-conflicting-outputs
```

### CI canonical command (GitLab + GitHub Actions)

```bash
flutter pub get
(cd core && flutter pub get)
flutter test --coverage --no-pub   # GitHub Actions
# GitLab .gitlab-ci.yml uses: flutter test --coverage
```

### Integration / E2E (standalone repo only — blocked in monorepo copy)

```bash
# Documented in CONTRIBUTING.md / CLAUDE.md but NOT in this copy's pubspec:
flutter test integration_test/
```

---

## 4. Coverage

| Item | Value |
|------|-------|
| **Tool** | `flutter test --coverage` → `coverage/lcov.info` |
| **Local threshold script** | `./scripts/check-coverage.sh` — default **30%** |
| **Makefile comment** | Says min **50%** (`Makefile` line 27) — inconsistent with CI |
| **CI threshold (GitLab + GitHub)** | **4%** line coverage regression floor |
| **Docs/testing-guide.md** | States **30%** CI threshold — **stale** (actual CI is 4%) |

### Verified Findings (this run)

```bash
flutter test --coverage
# Summary line:
# 02:21 +2412 -30: Some tests failed.

# Coverage parsed from coverage/lcov.info:
# Line coverage: 8% (9100/111277 lines)
```

The 8% measured coverage exceeds the CI floor of 4%, but **CI would still fail** because 30 individual test cases failed to pass.

---

## 5. Failing Tests

### Verified run summary

| Metric | Result |
|--------|--------|
| **Command** | `flutter test --coverage` |
| **Duration** | ~2 min 21 s |
| **Passed** | 2412 |
| **Failed** | 30 |
| **Exit code** | 1 |

### Failure groups and interpretation

#### A. Missing Mockito generated files (compile/load failures) — **env/setup, not logic bugs**

Tests import `*.mocks.dart` that were not generated. Fix: run `dart run build_runner build --delete-conflicting-outputs`.

| Test file | Blocker |
|-----------|---------|
| `test/core/system/user_font_scaling_sync_test.dart` | Missing `user_font_scaling_sync_test.mocks.dart` |
| `test/features/TFCOptions/presentation/viewmodels/trade_from_charts_viewmodel_test.dart` | Missing `.mocks.dart`; also undefined `tradeFromChartsViewModelProvider` |
| `test/features/research_ideas/.../research_ideas_order_flow_handler_test.dart` | Missing `.mocks.dart` |
| `test/features/company_page/.../chart_web_view_controller_test.dart` | Missing `.mocks.dart` |
| `test/features/mtf_statement/mtf_statement_vm_test.dart` | Missing `.mocks.dart` |
| `test/features/mtf_statement/mtf_margin_date_range_rules_test.dart` | Missing `.mocks.dart` |
| `test/features/company_page/.../fetch_company_details_usecase_test.dart` | Missing `.mocks.dart` |
| `test/features/portfolio_analytics/.../pml_portfolio_analytics_overview_viewmodel_test.dart` | Missing `.mocks.dart` |

#### B. Empty or incomplete test files (no `main()`) — **test debt**

| Test file | Error |
|-----------|-------|
| `test/features/TFCOptions/state/sealed_states_test.dart` | `Undefined name 'main'` |
| `test/features/TFCOptions/presentation/viewmodels/tfc_search_viewmodel_test.dart` | `Undefined name 'main'` |
| `test/features/TFCOptions/presentation/viewmodels/news_viewmodel_test.dart` | `Undefined name 'main'` |
| `test/features/TFCOptions/presentation/viewmodels/watchlist_viewmodel_test.dart` | `Undefined name 'main'` |

Interpretation: placeholder/stub files checked in without implementation; they break the full suite.

#### C. SSL pinning configuration — **real security vs test expectation**

| Test | Failure |
|------|---------|
| `test/core/network/ssl_config_test.dart` | `allowedCertificateHashes` is `[]`; test expects non-empty hashes |

Interpretation: production `SslConfig` has empty certificate hashes (pinning bypass). Test correctly flags a security gap documented in archived maturity reports.

#### D. Corporate events display formatting — **implementation changed, tests not updated**

| Test file | Expected vs actual |
|-----------|-------------------|
| `corporate_event_entity_test.dart` (3 cases) | Expected `₹2.50 per share`; actual `₹2.50/share` or `-` |
| `corporate_events_remote_datasource_test.dart` | Expected `₹5.50 per share`; actual `₹5.50/share` |
| `corporate_events_detail_integration_test.dart` | Expected `₹10.00 per share`; actual `-` |
| `event_description_formatter_test.dart` (3 cases) | Dividend string format mismatch |

Interpretation: `displayValue` / formatter logic changed; tests assert old copy. Likely a recent feature change, not environmental.

#### E. Widget / screen tests — **assertion failures (need individual triage)**

| Test file | Failing cases |
|-----------|---------------|
| `test/features/portfolios/.../portfolio_card_widget_test.dart` | 5 widget tests (display, visibility, graph tap, error state, masking) |
| `test/features/mtf_statement/delayed_payment_charges_screen_test.dart` | Screen rendering assertions |
| `test/features/mtf_statement/beneficiary_demat_charges_screen_test.dart` | 2 cases including "populated state lists history rows" |

Interpretation: UI/widget expectations may be out of date with current widgets or missing test harness setup (Riverpod overrides, theme, etc.).

#### F. Other assertion failure

| Test file | Notes |
|-----------|-------|
| `test/features/research_ideas/data/models/filter_count_calculator_test.dart` | Assertion failure — logic or fixture drift |

### Single-file smoke test (verified green)

```bash
flutter test test/core/utils/date_time_utils_test.dart
# 00:10 +37: All tests passed!
```

---

## 6. Test Health Assessment

### CI gating

| Gate | Enforced? | Evidence |
|------|-----------|----------|
| `flutter test` | Yes | `.gitlab-ci.yml` `test:` job; `.github/workflows/flutter-ci.yml` `test:` job |
| Coverage floor | Yes — **4%** | Both CI files parse `coverage/lcov.info` and fail below threshold |
| `flutter analyze` | Yes — errors fatal | `--no-fatal-infos --no-fatal-warnings` |
| Format check | Yes | `dart format --set-exit-if-changed .` |
| Dependency audit | Yes | `dart pub audit` |
| E2E in CI | NOT FOUND IN REPOSITORY | No CI job runs `integration_test/` |

### Coverage gaps

- **8% line coverage** vs aspirational **90%+ unit / 80%+ integration** in `docs/testing-guide.md`.
- Many feature modules under `lib/features/` have zero or stub tests (e.g. `TFCOptions` viewmodel stubs).
- Widget test coverage is thin relative to screen count (~25 widget test files vs hundreds of screens).
- `core/` package has no `core/test/` tree.

### Documentation inconsistencies

| Doc | Says | Reality |
|-----|------|---------|
| `docs/testing-guide.md` | CI threshold 30% | CI uses **4%** |
| `Makefile` | coverage min 50% | CI uses **4%**; script default **30%** |
| `CONTRIBUTING.md` | `flutter test integration_test/` works | **`integration_test` not in pubspec** (monorepo copy) |

### Slow / flaky signals

- Full suite ~2–3 minutes locally (2412 tests) — acceptable.
- No explicit `@Tags('flaky')` or retry config found.
- Logger output during tests is noisy but does not fail tests.

### Positive signals

- Large, meaningful unit test corpus (2400+ passing cases).
- CI runs analyze, format, test, coverage, audit, and web build smoke test.
- Established patterns documented in `docs/testing-guide.md` (model tests, `@GenerateMocks`, Riverpod overrides).

---

## 7. Recommendations

Prioritized improvements for a new engineer to get to green CI locally:

1. **Generate mocks before first full run** — add to onboarding/README: `dart run build_runner build --delete-conflicting-outputs`. Consider a CI step or pre-test hook so missing `.mocks.dart` never blocks the suite.

2. **Fix or quarantine stub test files** — remove or implement `TFCOptions` tests that lack `main()`, and complete or `@Skip` placeholder files. These alone cause 4 load failures.

3. **Resolve corporate events test drift** — align `displayValue` / `event_description_formatter` tests with current product copy (`₹X.XX/share` vs `₹X.XX per share`) or revert implementation to match approved spec.

4. **Reconcile coverage threshold docs** — single source of truth: CI uses 4%; update `docs/testing-guide.md`, `Makefile`, and `scripts/check-coverage.sh` comments to match, with a published roadmap for raising the floor (PM3-138617).

5. **Restore or document E2E path for monorepo** — either re-add `integration_test` to pubspec for standalone runs or document Maestro/native E2E as the monorepo canonical path (per `pubspec.yaml` comment).

6. **Address SSL pinning test failure** — populate `allowedCertificateHashes` or adjust test/environment split so security intent is clear (empty hashes = known risk).

7. **Triage failing widget tests** — portfolio card and MTF statement screens: update golden/widget expectations or fix provider/test harness setup.

---

## Appendix: CI config references

| File | Test-related content |
|------|---------------------|
| `.gitlab-ci.yml` | `flutter test --coverage`; 4% threshold; uploads `coverage/` artifact |
| `.github/workflows/flutter-ci.yml` | Same test + coverage job; parallel analyze/security/build jobs |
| `Makefile` | `test`, `coverage`, `coverage-html`, `check` |
| `scripts/check-coverage.sh` | Local coverage gate (default 30%) |
| `docs/testing-guide.md` | Patterns, commands, coverage targets |

---

## Agent Findings vs Verified Findings (summary)

### Agent Findings (from repo inspection)

- Framework: `flutter_test` + `mockito` + `build_runner`; Flutter 3.35.5.
- 211 unit/widget test files; 10 E2E files present but dep removed in monorepo copy.
- CI canonical command: `flutter test --coverage` with **4%** line floor.
- Coverage tooling: lcov via `--coverage`; optional `genhtml` via Makefile.

### Verified Findings (commands executed)

```text
# Smoke test
$ flutter test test/core/utils/date_time_utils_test.dart
00:10 +37: All tests passed!

# Full suite
$ flutter test --coverage
02:21 +2412 -30: Some tests failed.
Exit code: 1

# Coverage
Line coverage: 8% (9100/111277 lines)
```
