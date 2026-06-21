#!/usr/bin/env bash
# verify_trace.sh — assert every load-bearing edge of the I2 flow trace
# exists at the pinned commit of android-monorepo.
#
# Usage:
#   bash scripts/verify_trace.sh [path-to-android-monorepo-git-root]
#
# Repo resolution order:
#   1. $1 (CLI arg)            2. $ANDROID_MONOREPO env var
#   3. default local clone path (see DEFAULT_REPO below)
#
# Exit code 0 = all assertions pass at the pinned commit.
# Exit code 1 = one or more assertions failed (or repo/commit mismatch).
#
# An assertion passes if the expected substring is found AT the cited line,
# or within a +/- DRIFT_WINDOW line window (line drift is reported, not failed,
# so the trace survives small upstream edits while still flagging real breaks).

set -uo pipefail

PINNED_COMMIT="e7fc70a6b564ca3baffecb9a652194702443df3b"
DEFAULT_REPO="/Users/abhijeetpal/Desktop/workspace/android-monorepo/android-monorepo"
DRIFT_WINDOW=8

REPO="${1:-${ANDROID_MONOREPO:-$DEFAULT_REPO}}"

RED=$'\033[31m'; GRN=$'\033[32m'; YEL=$'\033[33m'; DIM=$'\033[2m'; RST=$'\033[0m'
pass=0; near=0; fail=0; misses=()

hr() { printf '%s\n' "------------------------------------------------------------"; }

echo "I2 flow-trace verifier"
hr
echo "Repo        : $REPO"
echo "Pinned SHA  : $PINNED_COMMIT"

if [[ ! -d "$REPO/.git" ]]; then
  echo "${RED}FATAL${RST}: '$REPO' is not a git repository."
  echo "Pass the android-monorepo git root as arg 1 or set \$ANDROID_MONOREPO."
  exit 1
fi

HEAD_SHA="$(git -C "$REPO" rev-parse HEAD 2>/dev/null || echo unknown)"
echo "Repo HEAD   : $HEAD_SHA"
if [[ "$HEAD_SHA" != "$PINNED_COMMIT" ]]; then
  echo "${YEL}WARN${RST}: HEAD != pinned commit. Line numbers were captured at the pinned"
  echo "      commit; results may show drift. Checkout the pin for an exact match:"
  echo "      git -C \"$REPO\" checkout $PINNED_COMMIT"
fi
hr

# assertion format: "relative/path.ext|LINE|expected substring"
ASSERTIONS=(
  # --- Flow A entry + GET ---
  "flutter/pml-flutter/lib/features/company_page/presentation/ui/PMLCompanyPage.dart|1829|_openWatchListBottomSheet"
  "flutter/pml-flutter/lib/features/company_page/presentation/ui/PMLCompanyPage.dart|1928|_openWatchListBottomSheet"
  "flutter/pml-flutter/lib/features/company_page/presentation/ui/bottom_sheets/PMLAddToWatchlistBottomSheet.dart|40|loadWatchList"
  "flutter/pml-flutter/lib/features/company_page/presentation/viewmodel/PMLWatchlistViewModel.dart|17|loadWatchList"
  "flutter/pml-flutter/lib/features/company_page/domain/usecases/PMLWatchlistUseCase.dart|11|fetchWatchlists"
  "flutter/pml-flutter/lib/features/company_page/data/repositories/PMLWatchlistRepositoryImpl.dart|13|fetchWatchlists"
  "flutter/pml-flutter/lib/features/company_page/data/datasources/remote/PMLWatchlistRemoteDataSourceImpl.dart|21|/marketwatch/api/v2/watchlist?verbose=1"
  # --- network: bridge default (resolves prior INFERRED hop) ---
  "flutter/pml-flutter/lib/core/network/api_manager.dart|33|_useBridge = false"
  "flutter/pml-flutter/lib/core/network/http_api_client.dart|428|ApiException"
  # --- Flow A POST ---
  "flutter/pml-flutter/lib/features/company_page/presentation/ui/bottom_sheets/PMLAddToWatchlistBottomSheet.dart|125|toggleWatchlistStatus"
  "flutter/pml-flutter/lib/features/company_page/presentation/viewmodel/PMLWatchlistViewModel.dart|135|addToWatchlist(watchlistId, securityId, watchListName)"
  "flutter/pml-flutter/lib/features/company_page/presentation/viewmodel/PMLWatchlistViewModel.dart|73|_useCase.addToWatchlist(watchlistId, securityId)"
  "flutter/pml-flutter/lib/features/company_page/data/datasources/remote/PMLWatchlistRemoteDataSourceImpl.dart|60|/marketwatch/api/v1/watchlist/\$watchlistId/security"
  "flutter/pml-flutter/lib/features/company_page/data/models/AddToWatchlistRequestBody.dart|8|'security_id': securityId"
  # --- Flow A post-success + native sync entry (resolves prior INFERRED hops) ---
  "flutter/pml-flutter/lib/features/company_page/presentation/viewmodel/PMLWatchlistViewModel.dart|74|onAddDeleteEvent"
  "flutter/pml-flutter/lib/features/company_page/presentation/di/PMLWatchlistProviders.dart|35|watchlistEventProvider.notifier).state = event"
  "flutter/pml-flutter/lib/features/company_page/presentation/ui/PMLCompanyPage.dart|807|watchlistEventProvider"
  "flutter/pml-flutter/lib/features/company_page/domain/usecases/PMLSendDetailsDataUseCase.dart|52|selectedTabType"
  "flutter/pml-flutter/lib/features/company_page/presentation/ui/PMLCompanyPage.dart|847|watchlistViewModelFamilyProvider(pmlID).notifier).loadWatchList()"
  "flutter/pml-flutter/lib/features/company_page/presentation/ui/PMLCompanyPage.dart|852|sync_watchlist"
  "flutter/pml-flutter/lib/core/bridge/usecases/pml_flutter_bridge_common_usecases.dart|170|handleDeeplink"
  "equity_sdk/src/main/java/com/paytmmoney/equity/flutter/FlutterNativeCommunicationImpl.kt|471|sync_watchlist"
  # --- Flow A native sync sub-trace -> Retrofit terminal ---
  "equity_sdk/src/main/java/com/paytmmoney/equity/watchlist/presentation/CachedWatchlistLiveData.kt|63|fun sync()"
  "equity_sdk/src/main/java/com/paytmmoney/equity/watchlist/domain/GetWatchlistUseCase.kt|29|getAllWatchlists"
  "equity_sdk/src/main/java/com/paytmmoney/equity/watchlist/data/RepositoryImpl.kt|38|getAllWatchlists(url, 1)"
  "equity_sdk/src/main/java/com/paytmmoney/equity/watchlist/data/CommonEquityWatchlistService.kt|17|@GET"
  # --- error paths ---
  "flutter/pml-flutter/lib/core/network/api_manager.dart|123|401"
  "flutter/pml-flutter/lib/core/network/api_manager.dart|126|419"
  "flutter/pml-flutter/lib/features/company_page/presentation/viewmodel/PMLWatchlistViewModel.dart|90|success: false"
  "equity_sdk/src/main/java/com/paytmmoney/equity/flutter/FlutterNativeCommunicationImpl.kt|472|runCatching"
  # --- base url + auth header merge ---
  "flutter/pml-flutter/lib/core/network/api_environment.dart|42|https://api-eq.paytmmoney.com"
  "flutter/pml-flutter/lib/core/network/header_config.dart|60|x-sso-token"
  "flutter/pml-flutter/lib/core/network/http_api_client.dart|359|addAll"
  # --- Flow B (recent-search) re-verification ---
  "equity_sdk/src/main/java/com/paytmmoney/equity/scripEvent/data/ScripEventRepositoryImp.kt|64|mergeArrayDelayError"
  "common-database/src/main/java/com/paytmmoney/equity_database/search/RecentSearchDao.kt|14|MAX = 10"
  "common-database/src/main/java/com/paytmmoney/equity_database/search/RecentSearch.kt|11|recent_search"
)

check() {
  local file="$1" line="$2" needle="$3" abs="$REPO/$1"
  if [[ ! -f "$abs" ]]; then
    fail=$((fail+1)); misses+=("MISSING FILE  $file"); printf '%s FAIL%s  %s  %s(no such file)%s\n' "$RED" "$RST" "$file" "$DIM" "$RST"; return
  fi
  # exact line?
  if sed -n "${line}p" "$abs" | grep -qF -- "$needle"; then
    pass=$((pass+1)); printf '%s ok  %s  %s:%s%s\n' "$GRN$RST" "" "$file" "$line" ""; return
  fi
  # within drift window?
  local lo=$((line>DRIFT_WINDOW ? line-DRIFT_WINDOW : 1)) hi=$((line+DRIFT_WINDOW))
  local hit
  hit=$(sed -n "${lo},${hi}p" "$abs" | grep -nF -- "$needle" | head -1 || true)
  if [[ -n "$hit" ]]; then
    local off=${hit%%:*}; local realline=$((lo+off-1))
    near=$((near+1)); printf '%s ~near%s %s:%s %s(found at ~%s, drift %+d)%s\n' "$YEL" "$RST" "$file" "$line" "$DIM" "$realline" "$((realline-line))" "$RST"; return
  fi
  fail=$((fail+1)); misses+=("NOT FOUND     $file:$line  «$needle»")
  printf '%s FAIL%s  %s:%s  %s«%s»%s\n' "$RED" "$RST" "$file" "$line" "$DIM" "$needle" "$RST"
}

echo "Asserting ${#ASSERTIONS[@]} trace edges..."
hr
for a in "${ASSERTIONS[@]}"; do
  IFS='|' read -r f l n <<< "$a"
  check "$f" "$l" "$n"
done
hr
printf 'Result: %s%d pass%s, %s%d near (drift)%s, %s%d fail%s  / %d total\n' \
  "$GRN" "$pass" "$RST" "$YEL" "$near" "$RST" "$RED" "$fail" "$RST" "${#ASSERTIONS[@]}"

if (( fail > 0 )); then
  echo; echo "${RED}Failures:${RST}"
  for m in "${misses[@]}"; do echo "  - $m"; done
  exit 1
fi
echo "${GRN}All trace edges verified.${RST}"
exit 0
