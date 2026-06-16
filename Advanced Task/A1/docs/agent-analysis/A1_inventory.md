# A1 — Repository / Artifact Inventory

**Agent:** A1 (Repository Inventory)
**Target:** `/Users/abhijeetpal/Desktop/workspace/android-monorepo`
**Date:** 2026-06-17
**Method:** Read `settings.gradle` + module `build.gradle` files; glob/grep on naming conventions. Equity vertical (`common-database/`, `equity_sdk/`, `base_app/`, `flutter/pml-flutter/`) read deeply; other modules counted only.

Each finding is labeled **VERIFIED** (directly read in a file), **INFERRED** (deduced from convention/structure), or **UNVERIFIED**.

---

## 1. Repository Overview

**VERIFIED** A single-repo Android monorepo (`rootProject.name = 'android-monorepo'`, `settings.gradle:35`) for the Paytm Money app. It is a multi-module Gradle build that bundles a native Kotlin equity trading SDK, a Room database module, MF (mutual-fund) feature modules, ~40 shared library modules, and a Flutter add-to-app integrated from source.

- **VERIFIED** Build orchestration: Gradle (Groovy DSL), root `build.gradle` (55 KB) defines a central `versions`/`deps` map. `gradlew`, `Makefile`, `build.sh`, CI via `.gitlab-ci.yml`, `bitbucket-pipelines.yml`, `Jenkinsfile`.
- **VERIFIED** App entry module is `:base_app` (holds `BaseApplication` + LAUNCHER activity); `:app` is an MF/library module consumed by `base_app`.
- **VERIFIED** Flutter integrated as source via add-to-app "Approach A": `settings.gradle:80-87` includes `:pml-flutter-library` (native wrapper) and evaluates `flutter/pml-flutter/.android/include_flutter.groovy`.
- **VERIFIED** 41 Gradle modules declared in `settings.gradle` (37 `include` lines + `:mf_features:*` sub-modules + `:pml-flutter-library` + Flutter source subproject).

---

## 2. Technology Stack (with manifest evidence)

| Layer | Technology | Version | Evidence |
|---|---|---|---|
| Language | Kotlin | 2.0.20 | `build.gradle:56` (`'kotlin':'2.0.20'`) |
| Build tool | Android Gradle Plugin | 8.9.1 | `build.gradle:24` (`'androidPlugin':'8.9.1'`); `settings.gradle:30-32` |
| SDK levels | minSdk 24 / compile 35 / target 35 | — | `build.gradle:20-22` |
| JVM target | Java 17 | — | `equity_sdk/build.gradle:130-131`; `compose.jvm_target='17'` (`build.gradle:5`) |
| UI (native) | Jetbrains Compose + View/DataBinding/ViewBinding | — | `equity_sdk/build.gradle:133-146`; `base_app/build.gradle:114-119` |
| DI | Dagger (kapt) + dagger-android | — | `equity_sdk/build.gradle:203-207`; DI dir `equity_sdk/.../equity/di/` (VERIFIED) |
| Persistence | Room (RxRoom + KTX) | — | `common-database/build.gradle:102-105`; `room.schemaLocation` arg `common-database/build.gradle:33` |
| Networking | Retrofit + OkHttp + Gson + RxJava adapter | — | `equity_sdk/build.gradle:264-267` |
| Async | RxJava/RxAndroid + Kotlin Coroutines | — | `equity_sdk/build.gradle:260-261,269-270` |
| Background | WorkManager (+ RxWorkManager) | — | `equity_sdk/build.gradle:300-301`; `base_app/build.gradle:279-280` |
| Firebase | BoM, Crashlytics, Performance, Messaging, App Indexing | — | `base_app/build.gradle:172-185`; `equity_sdk/build.gradle:199-201` |
| Analytics/3P | CleverTap, Paytm Signal SDK, Phoenix, AppsFlyer | — | `equity_sdk/build.gradle:298,303-304`; `base_app/build.gradle:286-288` |
| Media | ExoPlayer, CameraX + ML Kit barcode | — | `equity_sdk/build.gradle:305`; `base_app/build.gradle:272-276` |
| Cross-platform | Flutter (add-to-app, source) | Dart SDK >=3.0.0 <4.0.0; app v5.0.0+2 | `flutter/pml-flutter/pubspec.yaml` (`name: flutter_pml_app`) |
| Quality | detekt, ktlint, SonarQube, JaCoCo, lefthook | — | `equity_sdk/build.gradle:1-9,308-389`; `lefthook.yml` |
| Testing | JUnit, Mockito, MockK, Robolectric, MockWebServer, Espresso, Compose UI test | — | `equity_sdk/build.gradle:212-241` |

**VERIFIED** SDK artifact id `paytmmoney-equity`, version baseline `0.1.42-EQUITY-1.0.6-mtf-strip-v5` (`equity_sdk/build.gradle:14-15`). DB artifact `paytmmoney-database` v `0.0.22-database-1.0.1` (`common-database/build.gradle:10-11`).
**VERIFIED** App `versionCode 1306`, `versionName 9.85.0525`, applicationId `com.paytmmoney` (`base_app/build.gradle:48-52`). Four product flavors: `development`, `staging`, `production`, `preprod` (`base_app/build.gradle:87-108`, `equity_sdk/build.gradle:61-127`).

---

## 3. Module Inventory

In-scope (equity vertical) modules read deeply; others summarized. Source from `settings.gradle:37-87` and each module's `build.gradle`.

| Module | Responsibility | Key deps (selected) | Entry point / type |
|---|---|---|---|
| `:base_app` | **VERIFIED** App shell: hosts `BaseApplication`, LAUNCHER activity, home/dashboard, notifications, deeplink. `com.android.application` | `:app`, `:equity`, `:compose-home`, `:mf_features:*`, Firebase, CleverTap | `BaseApplication` (`base_app/src/main/java/com/paytmmoney/app/BaseApplication.kt:54`); launcher in `base_app/src/main/AndroidManifest.xml:34-37` |
| `:equity_sdk` | **VERIFIED** Equity/F&O trading SDK: orders, portfolio, watchlist, charts, search, market data, MTF, SIP, KYC flows. ns `com.paytmmoney.equity` (`equity_sdk/build.gradle:21`) | Dagger, Room, Retrofit, RxJava, Coroutines, Compose, `:common-database`, `:wsclient`, 20+ PML libs | Dagger components in `equity/di/` + `equity/boot/`; not an Application (library AAR) |
| `:common-database` | **VERIFIED** Room persistence layer. ns `com.paytmmoney.equity_database` (`common-database/build.gradle:17`). 24 `@Entity`, 24 `@Dao`, single `@Database` | Room (Rx/KTX), Dagger, `:core` | `EquityDatabase` (`common-database/.../EquityDatabase.kt`); `RoomModule` (per base_app comment, `base_app/build.gradle:281`) |
| `:pml-flutter-library` | **VERIFIED** Native Kotlin wrapper around Flutter engine (FlutterEngineGroup, bridge, webview asset loaders). ns `com.paytmmoney.pml_flutter_library` | Flutter embedding | `flutter/pml-flutter-library/src/main/.../FlutterEngineManager.kt`, `PMLFlutterActivity.kt`, `PMLFlutterBridge.kt` |
| `flutter/pml-flutter` (`:flutter`) | **VERIFIED** Dart Flutter module `flutter_pml_app` v5.0.0+2 — 18 feature areas, 2350 `.dart` files. Source-built Gradle subproject | webview_flutter, agentic_sdk | Dart `lib/main*.dart` (INFERRED) |
| `:app` | **VERIFIED (count)** MF/library aggregate consumed by base_app; 856 src files | (out of deep scope) | n/a |
| `:mf_features:{goals,amc,nfo,nps,portfolioSwitch,payment}` | **INFERRED** Mutual-fund feature modules; `:payment` is a dynamic feature (`base_app/build.gradle:152`) | — | n/a |
| `:compose-home` | **VERIFIED (count)** Compose home screens; 208 files | — | n/a |
| `:library` | **VERIFIED (count)** Largest shared lib; 391 files | — | n/a |
| `:subspayments` | **VERIFIED (count)** Subscription/payments; 197 files | — | n/a |
| `:bank` | **VERIFIED (count)** Banking; 138 files | — | n/a |
| `:supreme` | **VERIFIED (count)** Core/base utilities ("supreme"); 115 files | — | n/a |
| `:widgets` | **VERIFIED (count)** Shared widgets; 122 files | — | n/a |
| `:compose-core` | **VERIFIED (count)** Compose design system core; 98 files | — | n/a |
| `:digilocker` | 53 files | — | n/a |
| `:mini` | 51 files (mini-apps) | — | n/a |
| `:userkyc` | 41 files | — | n/a |
| `:crop`,`:apprating`,`:authentication`,`:txnstatus` | 31 / 30 / 27 / 27 files | — | n/a |
| `:wsclient`,`:manch_lib`,`:deeplink`,`:analytics` | 18 / 18 / 14 / 13 files (websocket, deeplink, analytics) | — | n/a |
| `:commonui`,`:customwidget`,`:customersupport`,`:currentlocation`,`:videoPlayer`,`:keys-provider` | 16 / 8 / 6 / 3 / 2 / 2 files | — | n/a |
| `:ManchSDK` | **VERIFIED** 0 Kotlin/Java src (prebuilt/aar wrapper, INFERRED) | — | n/a |
| `:keys-annotations`,`:keys-processor`,`:deeplink-annotations`,`:deeplink-processor` | **INFERRED** KSP/kapt annotation+processor pairs (codegen for keys & deeplinks) | — | n/a |
| `:macrobenchmark` | **VERIFIED** Baseline-profile generation; consumed by `base_app` (`base_app/build.gradle:168`) | — | n/a |

*+ remaining out-of-scope modules listed above are all in `settings.gradle:37-87`.*

---

## 4. Artifact Inventory (equity vertical)

> Counts via glob on naming conventions across `*/src/main/java` (excludes `/build/`, `/test/`). Cited samples are representative; full sets live under the cited paths.

### 4.1 Entry points / bootstrap
| Artifact | Path | Label |
|---|---|---|
| `BaseApplication` (app Application, `onCreate` at :109) | `base_app/src/main/java/com/paytmmoney/app/BaseApplication.kt:54` | VERIFIED |
| LAUNCHER activity declaration | `base_app/src/main/AndroidManifest.xml:34-37` | VERIFIED |
| `BaseAppModule` (Dagger app module, provides `MfMainApplication`) | `base_app/src/main/java/com/paytmmoney/app/di/BaseAppModule.kt` | VERIFIED |
| `AppComponent` (Dagger component) | `app/src/main/java/com/paytmmoney/mf/di/component/AppComponent.kt` | VERIFIED |
| Equity boot DI: `EquitySplashComponent`, `EquitySplashModelModule` | `equity_sdk/.../equity/boot/di/` | VERIFIED |
| Equity base DI: `EquityBaseComponent`, `EquityBaseModule`, `BaseInjector`, `CoroutineScopeModule`, `TickerClientManagerModule` (+ scopes `FeatureScope`,`EquityBaseScope`,`PriceAlertsScope`) | `equity_sdk/.../equity/di/` | VERIFIED |
| Flutter engine bootstrap: `FlutterEngineManager`, `FlutterEngineGroupManager`, `PMLFlutterActivity`, `PMLFlutterBridge`, `PMLNativeBridgeManager` | `flutter/pml-flutter-library/src/main/java/com/paytmmoney/pml_flutter_library/` | VERIFIED |
| Equity activity/interactor entry: `PaytmMoneyActivity`, `PaytmMoneyApp`, `PaytmInteractor`, `DeeplinkActivity`, `SessionRedirectHandler` | `equity_sdk/.../equity/interactor/` | VERIFIED |

### 4.2 Room entities (`@Entity`) — common-database (24 total, VERIFIED)
| Entity | Path |
|---|---|
| `RecentlyViewed` | `common-database/.../recentlyviewed/RecentlyViewed.kt` |
| `KycStatusEntity` | `common-database/.../kyc/KycStatusEntity.kt` |
| `PersonalDetails` | `common-database/.../userDetails/PersonalDetails.kt` |
| `EquityConfig` | `common-database/.../config/EquityConfig.kt` |
| `MtfScrips` | `common-database/.../mtf/MtfScrips.kt` |
| `FnoRanges`,`EquityRanges`,`TimeIntervals`,`AdvancedChartTypes`,`Indicators`,`YAxisScale`,`ChartTypes` | `common-database/.../chartconfigs/**` |
| `RecentSearch`,`MostInvestedStock`,`PopularSearch` | `common-database/.../search/` |
| `NotificationEntity` | `common-database/.../notificationcenter/NotificationEntity.kt` |
| `SleekCardDetails` | `common-database/.../sleekcard/SleekCardDetails.kt` |
| `CommonEntity`,`PortfolioEntity` | `common-database/.../homedashboard/{common,portfolio}/` |
| `HomeShortCut` | `common-database/.../homeshortcutdb/HomeShortCut.kt` |
| `EquityRealisedDetail`,`EquityRealisedSummary`,`FnoRealisedDetail`,`FnoRealisedSummary` | `common-database/.../pnL/` |

### 4.3 DAOs (`@Dao`) — common-database (24 total, VERIFIED)
`RecentlyViewedDao`, `KycStatusDao`, `PersonalDetailsDao`, `EquityConfigDao`, `MtfScripsDao`, `FnoRangesDao`, `EquityRangesDao`, `TimeIntervalsDao`, `AdvancedChartTypesDao`, `IndicatorsDao`, `YAxisScaleDao`, `ChartTypesDao`, `MostInvestedDao`, `RecentSearchDao`, `PopularSearchDao` **+9 more in** `common-database/src/main/java/com/paytmmoney/equity_database/**` (incl. `PMLNotificationDao`, `SleekCardDetailsDao`, `CommonDAO`, `PortfolioDAO`, `HomeShortCutDao`, 4 pnL DAOs). Single `@Database`: `EquityDatabase` (`common-database/.../EquityDatabase.kt`, VERIFIED).

### 4.4 ViewModels / state holders — `*ViewModel.kt` (VERIFIED counts)
- equity_sdk: **185** files; base_app: **9** files. Spread across feature packages (`watchlist`, `portfolio`, `orders`, `placeorder`, `charts`, `search`, `dashboard`, `funds`, `marginpledge`, `sip`, `marketmovers`, `indices`, etc. — see §4.10 package list).
- Sample: feature ViewModels under `equity_sdk/src/main/java/com/paytmmoney/equity/<feature>/...ViewModel.kt`. **+176 more in** `equity_sdk/src/main/java/com/paytmmoney/equity/`.
- **INFERRED** Flutter side uses Bloc/Cubit/ChangeNotifier state holders: **234** dart files matching `extends Bloc|Cubit|ChangeNotifier|StateNotifier` in `flutter/pml-flutter/lib`.

### 4.5 Repositories (interface + impl) — equity_sdk (VERIFIED counts)
- Files matching `*Repo.kt|*Repository.kt`: **86** (interfaces, domain layer). `*RepoImpl.kt|*RepositoryImpl.kt`: **65** (impls, data layer). base_app: **10** repo files.
- Representative pairs (interface in `domain/`, impl in `data/`):
  - `BootApiRepo` / `BootApiRepoImpl` — `equity_sdk/.../equity/boot/{domain,data}/`
  - `PushNotificationRepo` / `PushNotificationRepoImp` — `equity_sdk/.../equity/boot/{domain,data}/`
  - `TncUpdateRepo` / `TncUpdateRepoImpl` — `equity_sdk/.../equity/boot/{domain,data}/`
  - `EquityTraderConfigRepository` — `equity_sdk/.../equity/traders/domain/repository/`
  - Clean-arch repos under `equity/watchlist/{domain,data,mapper}/` (VERIFIED dirs)
  - **+80 more in** `equity_sdk/src/main/java/com/paytmmoney/equity/**`.
- **INFERRED** Flutter repositories: **149** `*repository*.dart` files in `flutter/pml-flutter/lib`.

### 4.6 Services / Retrofit API interfaces — equity_sdk (VERIFIED)
Files matching `*Service.kt|*Api.kt|*ApiService.kt`: **71**. Samples:
`BootApiService`, `PushNotificationService`, `TncService` (`equity/boot/data/`); `EquityOrderService` (`equity/placeorder/data/`); `CachedScripsService` (`equity/cachedScrips/data/repository/`); `IndexServices`, `EquityIndicesService` (`equity/indices/`); `PMLThreeIPOService`, `PMLThreeInvestmentIdeasService`, `MarginPledgeHoldingsService` (`equity/pmlthree/`); `MarketMoversIndicesServices` (`equity/marketmovers/data/`); `CAsService` (`equity/corporateActions/data/`); `EquityTraderAPIService` (`equity/traders/domain/repository/`); `PmlDetailsServices` (`equity/pmlDetails/data/`); `FnoRiskDisclosureService`, `OrderConfigService` **+56 more in** `equity_sdk/src/main/java/com/paytmmoney/equity/**`.

### 4.7 Use-cases / interactors — equity_sdk (VERIFIED)
Files matching `*UseCase.kt|*Interactor.kt`: **183**. Samples:
`BootApiUseCase`/`BootApiUseCaseImpl`, `PushNotificationUseCase`/`PushNotificationUseCaseImpl` (`equity/boot/domain/`); `EquityTraderConfigUseCase` (`equity/traders/usecase/`); core interactors `BaseUtility`, `PaytmInteractor`, `MiniActionUtilityImpl`, `EquityFlutterEngineManager`, `SupremeLogHandler` (`equity/interactor/`). **+178 more in** `equity_sdk/src/main/java/com/paytmmoney/equity/**`.

### 4.8 Jobs / workers / background (VERIFIED)
| Worker | Path | Label |
|---|---|---|
| `AppConfigWorker` (app config sync) | `equity_sdk/.../equity/dashboard/AppConfigWorker.kt` | VERIFIED |
| `UserBootWorker` (user boot tasks) | `base_app/src/main/java/com/paytmmoney/services/UserBootWorker.kt` | VERIFIED |
| `OrdersConfigTask` (config task; non-WM) | `equity_sdk/.../equity/configtask/OrdersConfigTask.kt` | VERIFIED |
| `LiveMarketNotificationLifecycleEvents` / managers (live-market notification lifecycle) | `base_app/.../livemarketnotification/` | VERIFIED |

Only 2 true `Worker`/`RxWorker` subclasses found across equity_sdk + base_app + common-database (grep on `: Worker|RxWorker|CoroutineWorker`). No Kafka/queue consumers — **NOT FOUND IN REPOSITORY** (mobile app; messaging is FCM/CleverTap push + websocket `:wsclient`).

### 4.9 Configs / feature flags (VERIFIED samples)
- BuildConfig URL/flavor configs: `equity_sdk/build.gradle:61-127` (per-flavor `EQUITY_*_URL`, `IBL_BASE_URL`, etc.).
- DB-backed config: `EquityConfig` entity + `EquityConfigDao` (`common-database/.../config/`).
- Code configs: `OrderPadConfigurations`, `BackpressureConfig`, `RetryConfig`, `FundConfig`, `AuthConfigDetails`, `WatchListTabConfig`, `HoldingsProductOfferingConfig`, `OrderConfigService`/`OrderConfigOutputModel` (`equity_sdk/.../equity/{util,extensions/coroutine,funds,data,watchlist/utils,portfolio/data,configtask}/`). Chart configs: `SavedConfigData`, `CompareChartConfig`, `MultiGridChartConfig`. **+ more `*Config*.kt` in** `equity_sdk/src/main/java/com/paytmmoney/equity/**`.
- No dedicated `FeatureFlag`/`RemoteConfig` class found by name — **NOT FOUND IN REPOSITORY** (flags appear handled via DB `EquityConfig` + BuildConfig; INFERRED).
- Root config files: `gradle.properties`, `*.properties` (development/staging/production), `local.properties` (holds `flutter.sdk`), `sonarqube.properties`.

### 4.10 Models / entities / DTOs — equity_sdk (VERIFIED counts)
- `*Response*.kt|*Request*.kt|*Model*.kt|*Dto*.kt`: **843** files (`*Response*.kt` alone: 80). Layered DTO↔domain mapping observed (e.g. `BootApiResponseDto` in `boot/data/bootapimodel/` ↔ `BootApiResponseDomainModel` in `boot/domain/bootapidomainmodel/`). **+ all under** `equity_sdk/src/main/java/com/paytmmoney/equity/**`.

### 4.11 Utilities (VERIFIED samples)
`equity/util/`, `equity/utils/`, `equity/extensions/` packages (VERIFIED dirs); `BaseUtility`, `AppsFlyerDeepLink`, `RetryConfig`, plus `base_app/.../utils/`. **+ many more in** `equity_sdk/src/main/java/com/paytmmoney/equity/{util,utils,extensions}/`.

### 4.12 Equity feature packages (VERIFIED — top-level under `equity_sdk/.../equity/`)
`boot`, `dashboard`, `portfolio`, `watchlist`, `orders`, `orderactions`, `orderdetail`, `orderBottomSheets`, `placeorder`, `search`, `scrip`, `scripEvent`, `companydetails`, `pmlDetails`, `charts`/`chart`/`mountaincharts`, `indices`, `marketmovers`, `marketdepth`, `markettimes`, `marginpledge`, `margincalculator`, `mtf`, `sip`, `funds`, `pricealerts`, `corporateActions`, `riskdisclosure`, `notificationpreferences`, `passcode`, `edis`, `accountstatement`, `traders`, `researchideas`, `pmlthree`, `tickerclient`, `cachedScrips`, `prefetchsetup`, `flutter`, `data`, `domain`, `interactor`, `di` **+ more (full set: 80+ packages)**.

### 4.13 Flutter feature areas (VERIFIED — `flutter/pml-flutter/lib/features/`)
`agentic_bot`, `basket_order`, `charts`, `company_page`, `corporateEvents`, `expert_picks`, `flash_trade`, `kyc`, `mtf_statement`, `options`, `orderpad`, `pledge`, `pml_orderpad`, `PMLWatchlist`, `portfolio_analytics`, `portfolios`, `research_ideas`, `TFCOptions` (18 features). `lib/` top dirs: `core`, `features`, `common`, `pmlcharts`, `generic`.

---

## 5. Counts Summary

| Metric | Count | Scope | Label |
|---|---|---|---|
| Gradle modules (`settings.gradle`) | 41 | whole repo (incl. `:mf_features:*`, flutter subprojects) | VERIFIED |
| Equity feature packages | 80+ top-level | equity_sdk | VERIFIED |
| Retrofit service interfaces (`*Service/*Api`) | 71 | equity_sdk | VERIFIED |
| Use-cases / interactors | 183 | equity_sdk | VERIFIED |
| Repositories — interfaces | 86 | equity_sdk | VERIFIED |
| Repositories — impls | 65 | equity_sdk | VERIFIED |
| ViewModels | 185 (equity_sdk) + 9 (base_app) = 194 | native | VERIFIED |
| Models/DTOs/Responses/Requests | 843 | equity_sdk | VERIFIED |
| Room entities (`@Entity`) | 24 | common-database | VERIFIED |
| Room DAOs (`@Dao`) | 24 | common-database | VERIFIED |
| Room databases (`@Database`) | 1 (`EquityDatabase`) | common-database | VERIFIED |
| DI components / modules | 58 components + 108 modules | equity_sdk | VERIFIED |
| WorkManager workers | 2 (`AppConfigWorker`, `UserBootWorker`) | equity_sdk + base_app | VERIFIED |
| Kotlin/Java src files (equity_sdk main) | 3,355 | equity_sdk | VERIFIED |
| Dart files | 2,350 | flutter/pml-flutter/lib | VERIFIED |
| Flutter state holders (Bloc/Cubit/Notifier) | 234 | flutter | INFERRED (name match) |
| Flutter repositories | 149 | flutter | INFERRED (name match) |
| Application entry points | 1 (`BaseApplication`) | base_app | VERIFIED |

**Notes / caveats:** Counts use filename conventions (glob/grep), so a file may belong to >1 logical category, and abstract base classes are included. Repository "interface" count (86) exceeds "impl" (65) because `*Repo.kt` glob also catches some non-pure-interface helpers; treat as upper bound. Out-of-scope modules counted by source-file totals only, not artifact-classified (per scope rules).
