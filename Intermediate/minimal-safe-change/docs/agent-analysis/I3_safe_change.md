# I3 — Small Safe Change (pml-flutter)

> Repository: `android-monorepo/flutter/pml-flutter`
> Branch: `fix/i3-date-string-yyyy-mm-dd-parse`
> Status: **IMPLEMENTED AND TEST-VERIFIED**

---

## 1. Problem Statement

`DateTimeUtils.dateStringToTimestamp()` returned a garbage negative timestamp when given
`YYYY-MM-DD HH:mm` input (e.g. `"2025-08-18 09:15"`) because the lenient `dd-MM-yyyy HH:mm`
DateFormat silently mis-parsed the year as the day before the ISO fallback could run.

---

## 2. Root Cause

**File:** `lib/core/utils/datetime_utils_internal.dart` — function `dtuDateStringToTimestamp` (lines 4–25)

The parser tried `DateFormat('dd-MM-yyyy HH:mm')` first. That formatter is lenient: it accepts
`2025-08-18 09:15` without throwing, interpreting `2025` as the day component. The nested
`yyyy-MM-dd HH:mm` catch block never executed, producing timestamp `-61405935300` instead of
`1755488700`.

An existing test explicitly documented this as known-broken behavior and directed callers to use
`dateStringToTimestampV2` instead.

---

## 3. Files Changed

| File | Reason |
|---|---|
| `lib/core/utils/datetime_utils_internal.dart` | Detect `YYYY-MM-DD HH:mm` via regex and parse with the correct formatter before the lenient DD-MM-YYYY attempt |
| `test/core/utils/date_time_utils_test.dart` | Flip the documented-bug test to assert correct parsing |
| `test/core/utils/datetime_utils_internal_test.dart` | New focused tests for `dtuDateStringToTimestamp` (required by TDD guard) |

---

## 4. Diff Summary

**Branch:** `fix/i3-date-string-yyyy-mm-dd-parse`

```diff
 int dtuDateStringToTimestamp(String dateString) {
   try {
+    // Try yyyy-MM-dd first — dd-MM-yyyy DateFormat is lenient and mis-parses ISO dates.
+    if (RegExp(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}').hasMatch(dateString)) {
+      final DateFormat formatter2 = DateFormat('yyyy-MM-dd HH:mm');
+      final DateTime parsedDate = formatter2.parse(dateString);
+      return parsedDate.millisecondsSinceEpoch ~/ 1000;
+    }
     try {
       final DateFormat formatter1 = DateFormat('dd-MM-yyyy HH:mm');
       ...
     } catch (e1) {
-      try { /* yyyy-MM-dd fallback — unreachable on lenient misparse */ }
-      catch (e2) { DateTime.parse(...) }
+      final DateTime parsedDate = DateTime.parse(dateString);
+      return parsedDate.millisecondsSinceEpoch ~/ 1000;
     }
```

**Hunk rationale:**
- **Regex guard:** Only routes space-separated `YYYY-MM-DD HH:mm` strings to the ISO formatter; ISO-8601 with `T` separator still falls through to `DateTime.parse`.
- **Removed nested try/catch:** The old inner fallback was dead code for the bug case because lenient parse never throws.
- **Test updates:** Assert equality instead of `isNot(equals(...))`; add direct unit tests on the internal function.

---

## 5. Test Results

### Before fix (failing)

```text
Command: flutter test test/core/utils/datetime_utils_internal_test.dart --name "parses YYYY-MM-DD HH:mm format"
Output:
  Expected: <1755488700>
    Actual: <-61405935300>
  Some tests failed.
```

### After fix (passing)

```text
Command: flutter test test/core/utils/datetime_utils_internal_test.dart test/core/utils/date_time_utils_test.dart
Output:
  00:05 +40: All tests passed!
```

### Lint

```text
Command: flutter analyze lib/core/utils/datetime_utils_internal.dart
Output:
  No issues found! (ran in 4.8s)
```

---

## 6. Risk Assessment

**Low**

- **Blast radius:** Single utility function used by chart view-models and data adapters (~15 call sites). DD-MM-YYYY and ISO-8601 (`T`) paths unchanged.
- **Consumers:** `PMLLiveChartViewModel`, `PMLAtmPcrChartViewModel`, `chart_data_adapter`, `prf_price_synchronizer` — all benefit from correct YYYY-MM-DD parsing via the shared `dateStringToTimestamp` API.
- **Coverage:** 40 tests in the two date-time test files; new test file adds direct coverage of the internal parser.

---

## 7. Rollback Plan

```bash
cd android-monorepo/flutter/pml-flutter
git checkout development
git branch -D fix/i3-date-string-yyyy-mm-dd-parse
```

Or, after merge: `git revert <commit-sha>`.

No database or persisted state changes — pure in-memory parsing logic.

---

## 8. Agent vs Verified

### Agent Suggested

- Identified the documented misparse in `date_time_utils_test.dart` as the fix target.
- Proposed routing `YYYY-MM-DD HH:mm` inputs to the ISO formatter before the lenient DD-MM-YYYY attempt.
- Created branch `fix/i3-date-string-yyyy-mm-dd-parse`.
- Added `datetime_utils_internal_test.dart` to satisfy the TDD guard hook.
- Refined regex after ISO-8601 regression (`T` separator must still use `DateTime.parse`).

### Manually Verified

- Baseline failure reproduced: `Actual: <-61405935300>` on YYYY-MM-DD input.
- Post-fix: `flutter test test/core/utils/datetime_utils_internal_test.dart test/core/utils/date_time_utils_test.dart` → **40/40 passed**.
- `flutter analyze lib/core/utils/datetime_utils_internal.dart` → **No issues found**.
- Caller search via grep confirmed ~15 usages of `dateStringToTimestamp`; no signature changes.
