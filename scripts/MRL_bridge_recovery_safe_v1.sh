#!/usr/bin/env bash
# MRL_bridge_recovery_safe_v1.sh
# origin_signature: MrLiouWord
# SUPPLEMENT_EXISTING: non-mutating entry beside MRL_bridge_recovery_run.sh.
# GET /health and /version only; never infer DL580 runtime state from HTTP alone.
# Optional auth: MRL_BRIDGE_KEY, passed as x-api-key through curl stdin config.
# Usage: bash scripts/MRL_bridge_recovery_safe_v1.sh [all|health|version]
# Requires bash, curl, awk. Body, cookies, credentials and raw headers are not printed.

set +x
set +v
set -uo pipefail

BRIDGE='https://bridge.mrliouword.com'
MODE="${1:-all}"
TIMEOUT="${MRL_TIMEOUT:-30}"
AUTH='false'
if [[ ! "$TIMEOUT" =~ ^([1-9]|[1-5][0-9]|60)$ ]]; then printf '%s\n' 'Invalid MRL_TIMEOUT; use 1 to 60 seconds.' >&2; exit 2; fi
case "$MODE" in all|health|version) ;; *) printf '%s\n' 'Usage: MRL_bridge_recovery_safe_v1.sh [all|health|version]' >&2; exit 2;; esac
for executable in curl awk; do
  if ! command -v "$executable" >/dev/null 2>&1; then printf 'Missing dependency: %s\n' "$executable" >&2; exit 2; fi
done
case "${MRL_BRIDGE_KEY:-}" in *$'\r'*|*$'\n'*) printf '%s\n' 'Invalid credential format.' >&2; exit 2;; esac
if [[ -n "${MRL_BRIDGE_KEY:-}" ]]; then AUTH='true'; fi

curl_config() {
  if [[ "$AUTH" == 'true' ]]; then
    local escaped="$MRL_BRIDGE_KEY"
    escaped="${escaped//\\/\\\\}"
    escaped="${escaped//\"/\\\"}"
    printf 'header = "x-api-key: %s"\n' "$escaped"
  fi
}

probe() {
  local endpoint="$1" headers='' transport=0 summary='' status='000' edge='unknown' challenge='false' ray='false' result=''
  headers="$(curl_config | curl --config - --silent --request GET --user-agent 'MRL-Recovery-Validator/1.0 (+https://github.com/dofaromg/MRL_AI_SYSTEM)' --header 'Accept: application/json' --max-time "$TIMEOUT" --connect-timeout "$TIMEOUT" --proto '=https' --dump-header - --output /dev/null --write-out $'\nMRL_HTTP_STATUS %{http_code}\n' "$BRIDGE/$endpoint" 2>/dev/null)" || transport=$?
  summary="$(printf '%s\n' "$headers" | awk '
    BEGIN { status="000"; edge="unknown"; challenge="false"; ray="false"; }
    /^HTTP\// { edge="unknown"; challenge="false"; ray="false"; }
    { line=tolower($0); sub(/\r$/, "", line); }
    line ~ /^server:[ \t]*cloudflare[ \t]*$/ { edge="cloudflare"; }
    line ~ /^cf-mitigated:[ \t]*challenge[ \t]*$/ { challenge="true"; }
    line ~ /^cf-ray:/ { ray="true"; }
    /^MRL_HTTP_STATUS [0-9][0-9][0-9]$/ { status=$2; }
    END { printf "%s %s %s %s", status,edge,challenge,ray; }
  ')"
  read -r status edge challenge ray <<< "$summary"
  if (( transport != 0 )); then result='TRANSPORT_UNVERIFIED'
  elif [[ "$challenge" == 'true' ]]; then result='HTTP_CHALLENGE'
  elif [[ "$status" =~ ^2[0-9][0-9]$ ]]; then result='METADATA_HTTP_REACHABLE'
  elif [[ "$status" =~ ^3[0-9][0-9]$ ]]; then result='HTTP_REDIRECT_UNFOLLOWED'
  else result='HTTP_NOT_ACCEPTED'
  fi
  printf '{"origin_signature":"MrLiouWord","method":"GET","path":"/%s","http_status":%s,"curl_exit_code":%s,"auth_configured":%s,"edge_header":"%s","challenge_header":%s,"cf_ray_present":%s,"result":"%s","response_body":"NOT_RETURNED","dl580_runtime":"UNVERIFIED"}\n' \
    "$endpoint" "$((10#$status))" "$transport" "$AUTH" "$edge" "$challenge" "$ray" "$result"
  [[ "$result" == 'METADATA_HTTP_REACHABLE' ]]
}

failed=0
case "$MODE" in
  all) probe health || failed=1; probe version || failed=1 ;;
  health) probe health || failed=1 ;;
  version) probe version || failed=1 ;;
esac
exit "$failed"
