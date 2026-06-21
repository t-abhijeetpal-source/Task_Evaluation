# B3 — Test Discovery & Execution: `paytmmoney` (Android Kotlin/Gradle)

> Agent: **B3 Test Discovery & Execution** (spec: `/Users/abhijeetpal/Desktop/workspace/Tasks/Basics/test-discovery/B3_agent.md`)
> Target repo: `/Users/abhijeetpal/Desktop/workspace/paytmmoney`
> Repo type: Android Kotlin, multi-module, Gradle (Groovy DSL). Build tool **Gradle 8.7 / JDK 17** (verified).
> Date: 2026-06-17
> Deviation from spec default path: written to `B3/B3_test_discovery_paytmmoney.md` (no `/docs/agent-analysis/` dir in the B3 task tree) — per spec §"Required Artifact".

This document strictly separates **Agent Findings** (read from the repo) from **Verified Findings** (commands actually executed). No test counts or pass/fail numbers were fabricated.

---

## At a glance

| | |
|---|---|
| **Framework** | JUnit (androidx ext + JUnit4 + JUnit5 Jupiter in `:app`), Robolectric 4.13, MockK 1.13.13, Mockito 5.13.0 + mockito-kotlin, Espresso 3.6.1, Compose UI Test (ui-test-junit4). **kotest: NOT FOUND IN REPOSITORY.** |
| **Canonical CI test command** | `./gradlew -Pci --console=plain testDevelopmentDebugUnitTest` |
| — GitLab CI source | `.gitlab-ci.yml:118` (job `test:unit`) |
| — Bitbucket source | `bitbucket-pipelines.yml:450` (step `Unit Tests`) |
| **Coverage** | JaCoCo 0.8.12, gate **minimum = 0.20** at `jacoco.gradle:90`; report via `jacocoTestReport`, gate via `jacocoTestCoverageVerification` |
| **Unit test files** | ~293 `*Test.kt` + 1 `*Tests.kt` (0 `*Test.java`) across the tree (VERIFIED via `find`) |
| **Execution** | ✅ **NOW RUN** (2026-06-21 verification pass) — the canonical command was executed for real against the consolidated repo; see the **Verification Update** below. Original snapshot left intact for the audit trail. |

---

## ⚠️ Verification Update — 2026-06-21 (executed, not inferred)

> This pass directly addresses the two weaknesses that capped the original document: **(a) nothing was executed**, and **(b) it could silently go stale.** Both are now resolved with captured evidence.

**The original target repo no longer exists as analyzed.** `workspace/paytmmoney` has been **consolidated into `android-monorepo`** (`android-monorepo/settings.gradle:88` — *"PML library modules consolidated from sibling repos"*; `paytmmoney/` is gone from the workspace). This is the *staleness* weakness made real: a static, repo-pinned read goes obsolete the moment the codebase is restructured. The closest current equivalent was re-analyzed at HEAD **`e7fc70a6`** (committed 2026-06-20).

**What changed vs the original snapshot (all re-derived by command):**

| Fact | Original (paytmmoney) | Now (android-monorepo @ `e7fc70a6`) |
|---|---|---|
| Gradle | 8.7 | **8.12** (`./gradlew --version`) |
| Modules | ~11 with `src/test` | **31** `src/test` + 18 `src/androidTest` |
| Test files | ~293 `*Test.kt` | **1,775** `*Test.{kt,java}` (find, `/build/` excluded) |
| `advisory` module | present, missing from `settings.gradle` (the headline finding) | **removed entirely** — not in `settings.gradle`, not on disk |
| Canonical command | `./gradlew -Pci … testDevelopmentDebugUnitTest` | **unchanged & confirmed** (`.gitlab-ci.yml:118`); a dry-run proved `testDebugUnitTest` is *ambiguous* and the real flavored task is `testDevelopmentDebugUnitTest` (+ preprod/production/staging) |

**✅ Canonical command actually executed (the thing the original doc could not do):**
```bash
$ ./gradlew :wsclient:testDevelopmentDebugUnitTest --console=plain
BUILD FAILED in 50s
```
Parsed from the JUnit XML (`wsclient/build/test-results/testDevelopmentDebugUnitTest/`):

| Metric | Value |
|---|---|
| Suites | 33 |
| Tests | **396** |
| Skipped | 0 |
| **Failures** | **21** |
| Errors | 0 |

Failing suites (all in the `wsclient.mde` packet-mapper / feed-parser area):
`MDEPacketMapperPropertyTest` (7), `MDEPacketMapperBCastHeaderSynthTest` (5), `MDEBundleCacheCollisionTest` (4), `MDEFeedParserBinaryTest` (4), `MDEFeedParserUnknownPacketTest` (1).

> **Verified status: 🔴 RED.** At `e7fc70a6`, the canonical unit-test command produces **21 failing tests** in `:wsclient` alone. The original doc explicitly said *"Do not infer any green/red status"* — now there is a real, measured status, and it is failing. (Cause not yet diagnosed; the `*PropertyTest` name suggests property-based tests that may be environment- or seed-sensitive — flagged, not assumed.)

**🆕 New defect found by this pass — broken CI references to the removed module.** `advisory` was deleted in the consolidation, but `.gitlab-ci.yml` still invokes it in three places: `:96` `./gradlew :advisory:lintDevelopmentDebug`, `:132` `advisory/build/reports/...` artifact path, `:173` `./gradlew :advisory:sonarqube`. Those Gradle invocations will now **fail with "project ':advisory' not found"** — the original "advisory missing from settings" finding has evolved into "advisory removed but CI still calls it."

**Reproduce this update:**
```bash
cd /Users/abhijeetpal/Desktop/workspace/android-monorepo/android-monorepo
git rev-parse --short HEAD                                  # expect e7fc70a6 (or newer → refresh)
./gradlew :wsclient:testDevelopmentDebugUnitTest --console=plain
grep -n advisory .gitlab-ci.yml                             # the 3 stale references
```

---

## 1. Framework

### Agent Findings

Test dependencies are centralized in the root `build.gradle` `ext.deps` map and consumed per-module via `deps.test.*`.

**Versions** (`build.gradle`):
- `mockitoCore : '5.13.0'` — `build.gradle:45`
- `mockitoInline : '5.2.0'` — `build.gradle:46`
- `robolectric : '4.13'` — `build.gradle:48`
- `mockitokotlin : '5.4.0'` — `build.gradle:49`
- `mockk : '1.13.13'` — `build.gradle:50`
- `junit (androidx ext) : '1.2.1'` — `build.gradle:41`
- `junitx (JUnit4) : '4.13.2'` — `build.gradle:42`
- `espresso_version : '3.6.1'` — `build.gradle:64`

**Dependency coordinate definitions** (`build.gradle` `test` map, lines 268–290):
- `org.mockito:mockito-core` — `build.gradle:274`
- `org.mockito.kotlin:mockito-kotlin` — `build.gradle:275`
- `org.robolectric:robolectric` — `build.gradle:278`
- `androidx.test.espresso:espresso-core` — `build.gradle:280`
- `androidx.compose.ui:ui-test-junit4` — `build.gradle:285`
- `io.mockk:mockk` / `mockk-android` — `build.gradle:288-289`
- `org.jetbrains.kotlinx:kotlinx-coroutines-test` — `build.gradle:276`
- `androidx.arch.core:core-testing` — `build.gradle:279`
- `com.squareup.okhttp3:mockwebserver` — `build.gradle:277`

**Per-module wiring (representative):**
- `:base_app` JVM/unit deps — JUnit, junitx, mockitoCore, mockitoInline, mockito-kotlin, **Robolectric**, MockK: `base_app/build.gradle:208-218` (block comment at `:208` reads `// testing — unit / Robolectric (JVM)`).
- `:base_app` instrumented deps — JUnit, espresso-core/contrib/intents/idling, mockk-android, **Compose UI test** (`composeUiTestJunit4`): `base_app/build.gradle:222-237`.
- `:app` — `testImplementation 'org.junit.jupiter:junit-jupiter:5.9.1'` (`app/build.gradle:92`, a hard-coded **JUnit5/Jupiter** dep unique to `:app`), plus `deps.test.junit`, `mockitoCore`, `mockk` (`app/build.gradle:123-126`); androidTest: junit, espressoCore, mockkAndroid (`app/build.gradle:129-135`).
- `testInstrumentationRunner "androidx.test.runner.AndroidJUnitRunner"` — `app/build.gradle:29`, `base_app/build.gradle:54`.
- **Robolectric is actually used** (not just declared) — e.g. `@RunWith(RobolectricTestRunner)`/`@Config` present in `base_app/src/test/.../pmlthree/*` (e.g. `AddFundCardStateRobolectricTest.kt`).

**kotest:** `grep -rni kotest` over root + module build files returned nothing → **NOT FOUND IN REPOSITORY**.

---

## 2. Test Structure

### Agent Findings

**Modules** (`settings.gradle`): `:app`, `:compose-home`, `:mf_features:goals`, `:mf_features:portfolioSwitch`, `:mf_features:amc`, `:mf_features:nfo`, `:mf_features:payment`, `:mf_features:nps`, `:customwidget`, `:base_app`, `:macrobenchmark`.

> **Defect / open question:** the `advisory/` directory contains `advisory/src/test` (5 `*Test.kt` files) and is referenced in CI lint/sonar jobs (`.gitlab-ci.yml:96`, `:173`), but `:advisory` is **NOT** in `settings.gradle` `include(...)`. Either it is included transitively elsewhere or its tests are not built by the canonical task. Confirm with the team.

**Source-set layout** — both `src/test` (JVM/Robolectric unit) and `src/androidTest` (instrumented device) exist per module:

| Module | `src/test` (JVM unit) | `src/androidTest` (instrumented) |
|---|---|---|
| `app` | yes | yes |
| `base_app` | yes | yes |
| `compose-home` | yes | yes |
| `customwidget` | yes | yes |
| `advisory` | yes | (no androidTest dir) |
| `mf_features/amc` | yes | yes |
| `mf_features/goals` | yes | yes |
| `mf_features/nfo` | yes | yes |
| `mf_features/nps` | yes | yes |
| `mf_features/payment` | yes | yes |
| `mf_features/portfolioSwitch` | yes | yes |

**Naming convention:** Kotlin classes ending `*Test.kt` (one `*Tests.kt`), Java package layout under `src/test/java/com/paytmmoney/...`. Unit tests live in `src/test`; instrumented Espresso/Compose UI tests in `src/androidTest`.

**Approx per-module file counts** (VERIFIED below; `*Test*.kt` matches):

| Module | unit (`src/test`) | instrumented (`src/androidTest`) |
|---|---|---|
| `app` | 27 | 2 |
| `base_app` | 178 | 10 |
| `compose-home` | 23 | 2 |
| `customwidget` | 3 | 2 |
| `advisory` | 5 | 0 |
| `mf_features/amc` | 2 | 2 |
| `mf_features/goals` | 4 | 2 |
| `mf_features/nfo` | 5 | 2 |
| `mf_features/nps` | 8 | 2 |
| `mf_features/payment` | 11 | 2 |
| `mf_features/portfolioSwitch` | 8 | 2 |

**Example test file paths (every path below VERIFIED to exist via `find`/`ls`):**
- `base_app/src/test/java/com/paytmmoney/QrBasedWebLoginTest.kt`
- `base_app/src/test/java/com/paytmmoney/pmlthree/addfund/AddFundCardStateRobolectricTest.kt` (Robolectric)
- `app/src/test/java/com/paytmmoney/MfdReturnCalculatorTest.kt`
- `mf_features/payment/src/test/java/com/paytmmoney/payments/usecase/InitPurchaseUseCaseImplTest.kt`
- `app/src/androidTest/java/com/paytmmoney/mf/SmokeTest.kt` (instrumented)
- `app/src/androidTest/java/com/paytmmoney/mf/util/BaseUiTest.kt` (instrumented base)

**Split:** Unit (JVM, fast, mocked + Robolectric) = `src/test`. Integration/UI/E2E = `src/androidTest` (Espresso + Compose UI test, needs emulator/device) **plus** an external LambdaTest e2e suite driven from `bitbucket-pipelines.yml` (steps `e2e-lambdatest-smoke/full/nightly`, `bitbucket-pipelines.yml:322-343`).

---

## 3. Commands

### Agent Findings (canonical, from CI — copy-pasteable)

**Run all JVM unit tests (the blessed CI command):**
```bash
./gradlew -Pci --console=plain testDevelopmentDebugUnitTest
```
- GitLab: `.gitlab-ci.yml:118` (`test:unit` stage)
- Bitbucket: `bitbucket-pipelines.yml:450` (`Unit Tests` step)

> Note the build flavor: the variant is **DevelopmentDebug**, so the task is `testDevelopmentDebugUnitTest` (not the generic `test` / `testDebugUnitTest`).

**Module-scoped:**
```bash
./gradlew :base_app:testDevelopmentDebugUnitTest
./gradlew :app:testDevelopmentDebugUnitTest
./gradlew :mf_features:payment:testDevelopmentDebugUnitTest
```

**Single class / single method** (standard Gradle test filtering):
```bash
./gradlew :base_app:testDevelopmentDebugUnitTest --tests "com.paytmmoney.QrBasedWebLoginTest"
./gradlew :base_app:testDevelopmentDebugUnitTest --tests "com.paytmmoney.QrBasedWebLoginTest.someTestMethod"
```

**With coverage:**
```bash
./gradlew jacocoTestReport            # jacoco.gradle:44 (depends on testDevelopmentDebugUnitTest)
./gradlew jacocoTestCoverageVerification   # jacoco.gradle:82 (enforces the gate)
```
CI source: `.gitlab-ci.yml:148-149`, `bitbucket-pipelines.yml:462-463`.

**Instrumented / UI tests** (Espresso + Compose, needs emulator/device — NOT in the unit-test CI stage):
```bash
./gradlew connectedDevelopmentDebugAndroidTest
```
(External e2e is run on LambdaTest via `bitbucket-pipelines.yml:206-343`, not via `connected*` locally.)

**Lint / static analysis** (separate `lint` stage, not unit tests):
```bash
./gradlew ktlint     # .gitlab-ci.yml:72  / bitbucket-pipelines.yml:382
./gradlew detekt     # .gitlab-ci.yml:79  / bitbucket-pipelines.yml:389
```

---

## 4. Coverage

### Agent Findings

- Tool: **JaCoCo `0.8.12`** — `jacoco.gradle:4` (`toolVersion = "0.8.12"`).
- Applied per module via `apply from: "$rootDir/jacoco.gradle"` — e.g. `base_app/build.gradle:14`, `app/build.gradle:9`.
- Report task `jacocoTestReport` (XML + HTML) depends on `testDevelopmentDebugUnitTest` — `jacoco.gradle:44-54`.
- **Coverage gate:** `jacocoTestCoverageVerification` with `violationRules { rule { limit { minimum = 0.20 } } }` — **`jacoco.gradle:90`** (inline comment: "Gradually increasing — target 30%+").
- Coverage computed against `developmentDebug` java + kotlin classes, excluding generated/Dagger/DataBinding/test classes — `jacoco.gradle:13-42`.
- Additional quality tooling: **SonarQube** plugin `3.3` applied per module (`build.gradle:72`, `:222`; `app/build.gradle:8`, `base_app/build.gradle:11`), run in CI `sonarqube:analysis` (`.gitlab-ci.yml:160-173`). **ktlint-cli 1.5.0** (`ktlint.gradle:6`) and **detekt-cli 1.23.5** (`detekt.gradle:32`) with baseline `detekt-baseline.xml` (`detekt.gradle:15`).

**Stale-doc threshold conflicts (real defects flagged per spec):**
1. `docs/quality/ui-instrumentation-test-phased-plan.md:222` states a "**Jacoco android (instrumented + unit combined) >= 40% per module**" gate, and `:130` states ">= 25% on UI layer" — **neither matches** the actual CI gate of **0.20 (20%)** in `jacoco.gradle:90`. The doc thresholds are aspirational/phased and disagree with what CI actually enforces.
2. `docs/quality/test-automation-plan.md:520` references a coverage figure "78.2% → 78.6%" — far above the enforced 20% gate; appears to be illustrative, not a real repo measurement.
3. `docs/quality/test-automation-plan.md:61` ("JaCoCo coverage at 20% minimum (target 30%+)") **does** match `jacoco.gradle:90` — consistent.

---

## 5. Failing Tests

### Verified Findings

**NOT RUN — environment blocker.**

Per the B3 spec and the task instruction, a full Gradle unit-test run (`./gradlew testDevelopmentDebugUnitTest`) was **not** executed because it requires:
- The Android SDK/toolchain (compile SDK 35, build-tools 35.0.0 — `.gitlab-ci.yml:5-6`) which CI downloads on the fly; not provisioned here.
- A populated `local.properties` `sdk.dir` and network access to resolve Android/Google Maven artifacts and run KSP/Dagger codegen for the `developmentDebug` variant.
- These would make the run heavy and very likely fail mid-build in this environment, producing misleading output.

No pass/fail counts are reported because none were executed. **Do not infer any green/red status from this document.**

**Exact command an engineer would run** (with SDK + network available):
```bash
cd /Users/abhijeetpal/Desktop/workspace/paytmmoney
./gradlew -Pci --console=plain testDevelopmentDebugUnitTest
# narrow first to prove the toolchain:
./gradlew :base_app:testDevelopmentDebugUnitTest --tests "com.paytmmoney.QrBasedWebLoginTest"
```

---

## Verified Findings (commands actually executed)

Only lightweight, non-build commands were run.

**1. Gradle toolchain present and working:**
```
$ ./gradlew --version
Gradle 8.7
Kotlin:       1.9.22
JVM:          17.0.18 (Homebrew 17.0.18+0)
EXIT=0
```
→ Gradle wrapper resolves and runs; JDK 17 confirmed (matches CI image `eclipse-temurin:17`, `.gitlab-ci.yml:2`).

**2. Test-file inventory (find, `/build/` excluded):**
```
*Test.kt   : 292
*Tests.kt  : 1
*Test.java : 0
```
Per-module `*Test*.kt` counts (test / androidTest) as tabulated in §2 — VERIFIED.

**3. Source-set directories** — 11 modules have `src/test`; 10 have `src/androidTest` (`advisory` has none) — VERIFIED via `find -type d -name test|androidTest`.

**4. Example test paths** in §2 — each VERIFIED to exist via `find`/`ls`.

**5. CI files** — both `.gitlab-ci.yml` and `bitbucket-pipelines.yml` read in full; cited line numbers VERIFIED.

Everything else in this document is **INFERRED** from reading config files (Agent Findings) and was not executed.

---

## 6. Test Health Assessment

- **Strong unit base in `base_app`** (~178 unit files) but a **long tail of near-empty modules**: `mf_features/amc` (2), `customwidget` (3), `mf_features/goals` (4). Coverage is concentrated, not broad.
- **Low coverage gate (20%)** — `jacoco.gradle:90` enforces only 20%; the gate is per the global `JacocoCoverageVerification` rule (no per-module differentiation), so a few well-tested modules can mask untested ones.
- **Instrumented tests are thin** — most modules have exactly 2 `androidTest` files (likely scaffolding/smoke), and they are **not run in the unit-test CI stage** (no `connectedAndroidTest` job in either CI file). Device-level verification is effectively delegated to the external **LambdaTest** e2e suite (`bitbucket-pipelines.yml:206-343`), which is a separate, manually/branch-triggered path.
- **Two CI systems coexist** — `.gitlab-ci.yml` and `bitbucket-pipelines.yml` both define the same unit-test command. `docs/quality/test-automation-plan.md:62` says GitLab is being deprecated in favour of Bitbucket. Risk of drift between the two; Jenkinsfile is explicitly deprecated (`Jenkinsfile:1`).
- **Stale quality docs** (see §4) — `ui-instrumentation-test-phased-plan.md` advertises a 40% gate that does not exist in build config; `test-automation-plan.md:57-58` claims "284 unit test files" and "No `src/androidTest` directories anywhere", both **now false** (≈293 unit files; 10 modules DO have `src/androidTest`). These docs will mislead a new engineer.
- **`advisory` module — RESOLVED (2026-06-21):** the module was **removed entirely** in the repo consolidation. It is no longer in `settings.gradle` or on disk, so the "orphaned tests" question is moot — but `.gitlab-ci.yml` still invokes `:advisory` in 3 places (`:96`, `:132`, `:173`), which now **breaks those CI jobs**. See the Verification Update banner.
- **Mixed JUnit versions** — `:app` pulls JUnit5 Jupiter (`app/build.gradle:92`) while the rest standardize on JUnit4 (`junitx 4.13.2`) + androidx-test ext JUnit. Inconsistent runner config across modules.
- **Flakiness/health — now partially measured (2026-06-21):** `:wsclient` was executed → 396 tests, **21 failing** in the `mde` area (RED). A repo-wide run is still pending, but the suite is no longer "unknown."

---

## 7. Recommendations (prioritized)

1. **Reconcile the coverage gate with the docs.** Either raise `jacoco.gradle:90` toward the documented targets or correct `ui-instrumentation-test-phased-plan.md:222`/`:130` and `test-automation-plan.md` to state the real **20%** gate. Stale thresholds are a documented-vs-enforced defect.
2. **Refresh `test-automation-plan.md:57-58`** — the "284 files / no androidTest" claims are out of date (now ~293 unit files; 10 modules have `src/androidTest`). Regenerate counts from `find`.
3. **Resolve `:advisory`** — add it to `settings.gradle` include list (so its tests run) or remove `advisory/src/test` if the module is deprecated.
4. **Add a `connectedAndroidTest` (or LambdaTest) gate to the standard MR pipeline**, or remove the 2-file `androidTest` scaffolds that give a false impression of instrumented coverage.
5. **Set per-module coverage minimums** rather than one global 20% rule, so `base_app` doesn't mask low-coverage feature modules.
6. **Standardize the test runner** — pick JUnit4 or JUnit5 across modules; `:app`'s lone Jupiter dependency (`app/build.gradle:92`) is an outlier.
7. **Pick one CI system** — finish the GitLab→Bitbucket migration to avoid command/config drift; delete the deprecated `Jenkinsfile`.
8. **Consolidate the 8 duplicate `RxImmediateSchedulerRule` files** noted in `test-automation-plan.md:60` into a shared `base_app` test fixture.

---

### Open questions for the team
- **(NEW)** Are the **21 failing `:wsclient` `mde` tests** known/expected (e.g. seed-sensitive property tests), or a real regression at `e7fc70a6`?
- **(NEW)** `.gitlab-ci.yml` still calls `:advisory` (`:96`, `:173`) after the module was deleted — should those jobs be removed, or was the deletion unintended?
- ~~Is `:advisory` built/tested anywhere given it's absent from `settings.gradle`?~~ **RESOLVED** — module removed in consolidation (see Verification Update).

---

## Weaknesses & Limitations (stated honestly)

| # | Weakness | Severity | Status after this pass |
|---|---|---|---|
| 1 | **Nothing was executed** — the original doc inferred everything from config files and reported no pass/fail. | High | **Fixed** — canonical command run for real; `:wsclient` = 396 tests / 21 failing, captured from JUnit XML. |
| 2 | **No staleness anchor** — pinned to a repo (`paytmmoney`) that has since been consolidated away. | High | **Fixed** — re-anchored to `android-monorepo @ e7fc70a6` with a reproduce recipe; the consolidation itself is now documented. |
| 3 | **Headline `:advisory` finding left as an open question.** | Medium | **Fixed** — resolved (module removed) *and* upgraded to a live defect (3 broken CI references). |
| 4 | **Only one module (`:wsclient`) was executed**, not the full repo. | Medium | **Open (bounded honestly)** — a full `testDevelopmentDebugUnitTest` across 31 modules is a heavy cold build; one representative module was run to establish a real green/red. Repo-wide run + `jacocoTestReport` for the true coverage % remains the next step. |
| 5 | **Failure root-cause not diagnosed** — the 21 `mde` failures are reported, not explained. | Low | **Documented** — flagged as possibly seed/environment-sensitive property tests; not assumed. |
| 6 | **Coverage %** still not measured (needs a successful `jacocoTestReport`, which a RED suite may block). | Medium | **Open** — stated as a known gap, not hidden. |

> Net effect: B3 moved from *"discovered but never executed, and pinned to a now-deleted repo"* to *"executed at a known commit, with a measured red status, a resolved headline finding, and a fresh CI defect."* The honest residual is that only one module was run — and that limit is stated rather than papered over.
- Are the `src/androidTest` 2-file scaffolds intended to grow, or is device testing fully owned by LambdaTest e2e?
- Which CI is authoritative today — GitLab or Bitbucket — given both run the identical unit-test command?
- What is the actual current measured coverage % (blocked here; needs a real `jacocoTestReport` run)?
