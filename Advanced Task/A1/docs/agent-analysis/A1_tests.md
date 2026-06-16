# A1 — Test Discovery (Agent 4)

**Target:** `/Users/abhijeetpal/Desktop/workspace/android-monorepo`
**Scope:** equity vertical (`common-database`, `equity_sdk`, `base_app`) + `flutter/pml-flutter` (Flutter package)
**Date:** 2026-06-17 · Confidence tags: VERIFIED (executed: file reads, `find` counts) / INFERRED / UNVERIFIED

> Execution blocker honored: no full Gradle/Flutter build was run (heavy, requires Android SDK + Flutter SDK, would fail in this environment). All findings below are from reading config files and counting source files. **No pass/fail counts are fabricated.**

---

## 1. Framework

### Kotlin / Android (versions resolved from the version catalog in root `build.gradle`)
All test deps are declared via a `deps.test.*` catalog defined in `build.gradle:272-292` with versions at `build.gradle:35-124`. VERIFIED.

| Framework | Coordinate | Version | Catalog line |
|---|---|---|---|
| JUnit4 | `junit:junit` (`junitx`) | 4.13.2 | `build.gradle:42`, `:274` |
| AndroidX JUnit ext | `androidx.test.ext:junit` | 1.2.1 | `build.gradle:41`, `:273` |
| Robolectric | `org.robolectric:robolectric` | 4.13 | `build.gradle:48`, `:281` |
| MockK | `io.mockk:mockk` / `mockk-android` | 1.13.13 | `build.gradle:50`, `:291-292` |
| Mockito | `mockito-core` / `mockito-inline` / `mockito-kotlin` | 5.13.0 / 5.2.0 / 5.4.0 | `build.gradle:45-49`, `:277-290` |
| Espresso | `androidx.test.espresso:*` (core/contrib/intents/idling) | 3.6.1 | `build.gradle:64`, `:283-286` |
| Compose UI test | `androidx.compose.ui:ui-test-junit4` / `ui-test-manifest` | 1.6.8 | `build.gradle:123`, `:288-289` |
| Coroutines test | `kotlinx-coroutines-test` | 1.7.3 (also pinned in equity_sdk) | `build.gradle:279`; `equity_sdk/build.gradle:225` |

Per-module declarations:
- `common-database/build.gradle:94-117` — JUnit, Mockito (core/inline/kotlin), Espresso (core/contrib). No MockK, no Robolectric.
- `equity_sdk/build.gradle:212-237` — Mockito + JUnit + Robolectric + **MockK 1.13.13 hard-pinned inline** (`mockk` + `mockk-agent-jvm`, JUnit5 excluded) + coroutines-test; androidTest uses Espresso + `mockk-android`.
- `base_app/build.gradle:209-234` — JUnit, JUnitX, Mockito (core/inline/kotlin), Robolectric, MockK; androidTest uses Espresso + `mockk-android`.

### Flutter (`flutter/pml-flutter/pubspec.yaml:71-82`) VERIFIED
- `flutter_test` (sdk: flutter) — `pubspec.yaml:74-75`
- `mockito: ^5.6.4` — `pubspec.yaml:81`
- `build_runner: ^2.6.0`, `json_serializable: ^6.7.1` (mock/codegen) — `pubspec.yaml:72,80`
- `fake_async: ^1.3.3` — `pubspec.yaml:73`
- `very_good_analysis: ^6.0.0` (lints) — `pubspec.yaml:82`
- **Note (`pubspec.yaml:76-79`):** `integration_test` and `patrol` were *removed* from the monorepo-embedded copy because their native Android subprojects break the add-to-app build; integration/patrol tests live in the standalone pml-flutter repo, and the monorepo tests natively via **Maestro**. INFERRED from comment.

---

## 2. Test Structure (per module, counts, example paths)

Counts from `find -name "*Test.kt"` / `*_test.dart` (VERIFIED). Whole-repo: **1684 `*Test.kt`**, **220 `*_test.dart`**.

| Module | `src/test` (JVM/Robolectric) | `src/androidTest` (instrumented) | Example path (verified to exist) |
|---|---|---|---|
| `common-database` | 5 | 26 | `common-database/src/test/java/test/ConvertersTest.kt` (VERIFIED exists) |
| `equity_sdk` | **303** | 4 | `equity_sdk/src/test/java/com/paytmmoney/equity/OrderBookViewModelTest.kt` (VERIFIED exists) |
| `base_app` | 172 | 10 | `base_app/src/test/java/com/paytmmoney/QrBasedWebLoginTest.kt` |

More verified example paths:
- JVM unit (Robolectric/MockK): `equity_sdk/src/test/java/com/paytmmoney/equity/BaseEquityViewModelTest.kt`, `equity_sdk/src/test/java/com/paytmmoney/equity/AIReviewReportTest.kt`
- common-database unit: `common-database/src/test/java/test/MtfScripsUtilTest.kt`, `.../PersonalDetailsTest.kt`
- common-database instrumented (Room): `common-database/src/androidTest/java/test/MigrationTest.kt`, `.../RoomModuleTest.kt`
- Espresso/Compose instrumented: `equity_sdk/src/androidTest/java/com/paytmmoney/equity/ui/SmokeUiTest.kt`, `equity_sdk/src/androidTest/java/com/paytmmoney/equity/compose/SmokeComposeTest.kt`, `base_app/src/androidTest/java/com/paytmmoney/compose/PortfolioReturnsSwitchComposeTest.kt`, `base_app/src/androidTest/java/com/paytmmoney/ui/DeeplinkActivityIntentTest.kt`
- Compose UI test rule base classes: `equity_sdk/src/androidTest/.../util/BaseComposeUiTest.kt`, `base_app/src/androidTest/.../util/BaseComposeUiTest.kt`

### Flutter (`flutter/pml-flutter/`) VERIFIED
- `test/` — **212** `*_test.dart` (unit + widget). Example: `flutter/pml-flutter/test/stock_model_serialization_test.dart` (VERIFIED exists)
- `integration_test/` — **6** files. Examples: `integration_test/smoke_test.dart`, `integration_test/app_test.dart`, `integration_test/flash_trade/flash_trade_landing_test.dart`
- `test_driver/integration_test.dart` (driver harness)
- `core/` package: **0** `*_test.dart` (no tests in the `core` sub-package). INFERRED gap.

---

## 3. Commands

### Canonical = what CI runs

**Bitbucket (active super-app pipeline, `bitbucket-pipelines.yml`)** — the unit-test stage: VERIFIED
- `bitbucket-pipelines.yml:707-713` — **"Unit Tests"** step:
  `./gradlew -Pci --console=plain :base_app:testProductionDebugUnitTest --no-daemon --max-workers=4`
- `bitbucket-pipelines.yml:720-727` — **"Coverage Report"** step:
  `./gradlew jacocoTestReport ...` then `./gradlew jacocoTestCoverageVerification ...` (both `|| true` — **non-blocking**).
- Flutter lint step exists (`bitbucket-pipelines.yml:675-686`: `flutter analyze`, `dart format`) but **there is NO `flutter test` step anywhere in `bitbucket-pipelines.yml`** (grep for `flutter test`/`--coverage`/`lcov` returned nothing). VERIFIED gap.

**GitLab (`.gitlab-ci.yml`)** — present but uses a *different* product flavor: VERIFIED
- `.gitlab-ci.yml:115-118` — `test:unit` stage: `./gradlew -Pci --console=plain testDevelopmentDebugUnitTest` (all modules, **Development** flavor — no module scoping).
- `.gitlab-ci.yml:144-149` — `coverage:report`: `./gradlew jacocoTestReport` + `./gradlew jacocoTestCoverageVerification`.
- JUnit reports collected at `**/build/test-results/testDevelopmentDebugUnitTest/TEST-*.xml` (`.gitlab-ci.yml:135-137`).

> **Discrepancy (UNVERIFIED which is authoritative):** GitLab runs `testDevelopmentDebugUnitTest` across *all* modules; Bitbucket runs only `:base_app:testProductionDebugUnitTest`. Bitbucket's flavor is **production**, GitLab's is **development**. equity_sdk's jacoco wiring (`equity_sdk/build.gradle:343,375`) and the root `jacoco.gradle` both key off `testDevelopmentDebugUnitTest.exec` — so the Bitbucket *production* unit-test exec files will NOT match the jacoco `executionData` includes, meaning coverage data for the production run is likely empty under Bitbucket. INFERRED defect.

### Module-scoped commands (from `docs/development/testing-guide.md:183-202`, INFERRED for equity scope)
- All JVM unit tests: `./gradlew test` (`testing-guide.md:183`)
- equity_sdk unit: `./gradlew :equity_sdk:testDevelopmentDebugUnitTest`
- base_app unit: `./gradlew :base_app:testDevelopmentDebugUnitTest` (CI uses `:base_app:testProductionDebugUnitTest`)
- common-database unit: `./gradlew :common-database:testDebugUnitTest` (library module — no product flavors; INFERRED)
- Single test: `./gradlew :app:testDevelopmentDebugUnitTest --tests "com.paytmmoney.viewmodel.FundViewModelTest"` (`testing-guide.md:194`)
- Instrumented (needs device/emulator): `./gradlew :equity_sdk:connectedDevelopmentDebugAndroidTest` (INFERRED — not run in CI)
- Coverage: `./gradlew jacocoTestReport` → `build/reports/jacoco/` (`testing-guide.md:199-202`)
- Flutter: `cd flutter/pml-flutter && flutter test` / `flutter test --coverage` (`flutter/pml-flutter/Makefile:9,29`, VERIFIED)

---

## 4. Coverage (jacoco)

- **Root `jacoco.gradle`** (applied by `base_app/build.gradle:14`): toolVersion **0.8.12** (`jacoco.gradle:4`). Threshold **minimum = 0.20** (20%) with comment "target 30%+" (`jacoco.gradle:88-90`). Tasks: `jacocoTestReport` (`:44`), `jacocoTestCoverageVerification` (`:82`). Keys off `testDevelopmentDebugUnitTest.exec` (`jacoco.gradle:76`).
- **equity_sdk** has its *own* jacoco block (`equity_sdk/build.gradle:308-377`), NOT the shared one: threshold **minimum = 0.10** (10%) — `equity_sdk/build.gradle:353` ("Start with 10% minimum, increase as tests are restored" — suggests tests were removed/disabled). Different task names (`jacocoCoverageVerification` vs root's `jacocoTestCoverageVerification`).
- **common-database** applies neither jacoco file (`common-database/build.gradle` applies only ktlint+detekt at `:5-6`) → **no coverage gate** for this module. VERIFIED gap.
- **Gate strength:** In Bitbucket the verification runs with `|| true` (`bitbucket-pipelines.yml:727`) → coverage is **report-only, non-blocking**. GitLab's `coverage:report` (`.gitlab-ci.yml:144-149`) does not append `|| true`, so there the verification *can* fail the pipeline. UNVERIFIED whether GitLab pipeline is still the active one.

### Stale documentation thresholds (flag)
- `docs/quality/test-automation-plan.md:61` says "JaCoCo coverage at 20% minimum (target 30%+)" — matches root `jacoco.gradle` (consistent).
- `docs/quality/test-automation-plan.md:520,549` cite concrete figures **"Coverage: 78.6%"** / "+0.4% (78.2% → 78.6%)" — these are **not** backed by any gate (gate is 20%/10%) and read as fabricated sample-log numbers. UNVERIFIED / likely stale-doc.
- `docs/quality/ui-instrumentation-test-phased-plan.md:130,222` set aspirational gates (">= 25%", ">= 40% per module, PR fails on negative delta") that are NOT implemented in either CI file. Stale/aspirational.
- `docs/architecture/monorepo-flutter-integration.md:331-359,627,641` reference the Flutter dir as **`flutter/pml_flutter`** (underscore) and `fvm flutter test`; the real dir is **`flutter/pml-flutter`** (hyphen) and the Makefile uses plain `flutter test`. Stale path in docs.

---

## 5. Execution status (BLOCKER)

**Not executed.** A full `./gradlew ...UnitTest` or `flutter test` was deliberately not run: it requires the Android SDK (CI downloads cmdline-tools `11076708`, platform `android-35`, build-tools `35.0.0` per `.gitlab-ci.yml:5-7,22-38`) and a Flutter SDK (`3.35.5` per `.flutter-version`, bootstrapped in `bitbucket-pipelines.yml:41-52`), plus `local.properties` injection. These are heavy and would fail without provisioned SDKs in this environment. No pass/fail or coverage-percentage numbers are reported as observed.

**Verified (trivial, executed):** all CI/config/build files read; test-file counts via `find`; existence of every example test path above confirmed via `ls`.

---

## 6. Test Health Assessment

- **Volume looks strong but is unevenly gated.** equity_sdk (303) + base_app (172) carry most JVM tests; common-database has only 5 unit tests vs 26 instrumented (DB migration-heavy, expected). Flutter has 212 unit/widget tests.
- **CI under-runs the suite.** Bitbucket (apparently the active pipeline) executes unit tests for `:base_app` **only** (`bitbucket-pipelines.yml:713`). The 303 equity_sdk and 220 Flutter tests are **never executed in the Bitbucket pipeline** — they exist but aren't gating merges. Major gap.
- **Flavor mismatch undermines coverage.** Bitbucket runs `testProductionDebug...` while jacoco's `executionData` only includes `testDevelopmentDebug...exec` (`jacoco.gradle:76`; `equity_sdk/build.gradle:343,375`) → coverage report likely empty under Bitbucket.
- **Coverage gates are weak/non-blocking.** Root 20%, equity_sdk 10%, common-database none; Bitbucket runs verification with `|| true`.
- **No Flutter test in CI at all** despite 212 tests and an existing `coverage/lcov.info` artifact — Flutter relies on local `make` / external repo / Maestro.
- **Instrumented tests not in CI.** Espresso/Compose UI tests (`*/src/androidTest`) require a device; no `connectedAndroidTest` stage in either CI file → smoke/Compose tests are dev-only.
- **Docs drift.** Coverage figures (78.6%), aspirational gates, and the `pml_flutter` path are stale relative to actual config.

---

## 7. Recommendations

1. **Run the full unit-test set in CI.** Add `:equity_sdk:` and `:common-database:` unit-test invocations to the Bitbucket "Unit Tests" step (currently `:base_app` only, `bitbucket-pipelines.yml:713`).
2. **Fix the flavor/exec mismatch.** Either run `testDevelopmentDebugUnitTest` in Bitbucket (to match jacoco's `executionData`) or update `jacoco.gradle:76` + `equity_sdk/build.gradle:343,375` to include the `testProductionDebugUnitTest.exec` path.
3. **Add a Flutter test step** (`cd flutter/pml-flutter && flutter test --coverage`) to `bitbucket-pipelines.yml`; 212 tests + an lcov config exist and are unused.
4. **Make coverage gating real.** Drop the `|| true` on `jacocoTestCoverageVerification` (`bitbucket-pipelines.yml:727`), give `common-database` a jacoco config, and converge equity_sdk's 10% toward the documented 20%/30% target.
5. **Reconcile dual CI.** Decide GitLab vs Bitbucket as canonical; they run different flavors/scopes and only one should gate.
6. **Update stale docs:** remove/replace the fabricated 78.6% figures (`test-automation-plan.md:520,549`), align aspirational gates with reality, and fix `pml_flutter` → `pml-flutter` paths (`monorepo-flutter-integration.md`).
7. **Add an instrumented smoke stage** (Espresso/Compose `connectedDebugAndroidTest` on an emulator/Firebase Test Lab) — the SmokeUiTest/SmokeComposeTest scaffolding already exists but never runs.
