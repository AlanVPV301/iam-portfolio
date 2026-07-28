#!/usr/bin/env bash
# Wake the deployed services and rebuild SCIM demo state from the HR CSV.
#
# Why this exists: Render free instances have an ephemeral filesystem and spin
# down after 15 minutes idle, so the SCIM database is empty every time the
# service wakes. Rather than fight that, the target system is treated as
# disposable and rebuilt from hr/demo-events.csv, which is the durable source of
# record because it lives in git.
#
# Run this at the start of a demo window (or from a scheduler), not overnight —
# whatever it writes is discarded 15 minutes after the last request.
#
# Prerequisites:
#   export ORCH_TOKEN="$(grep '^ORCHESTRATOR_BEARER_TOKEN=' .env | cut -d= -f2-)"
#   export SCIM_TOKEN="$(grep '^SCIM_BEARER_TOKEN=' .env | cut -d= -f2-)"
#   The venv must be active — import-hr-csv.py needs `requests`.
#
# Usage:
#   ./scripts/prime-demo.sh                    # against the public deployment
#   ORCH_URL=http://127.0.0.1:8000 SCIM_URL=http://127.0.0.1:8001 ./scripts/prime-demo.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ORCH_URL="${ORCH_URL:-https://jml.alanvpv.dev}"
SCIM_URL="${SCIM_URL:-https://scim.alanvpv.dev}"
ORCH_TOKEN="${ORCH_TOKEN:?Set ORCH_TOKEN from .env ORCHESTRATOR_BEARER_TOKEN}"
SCIM_TOKEN="${SCIM_TOKEN:?Set SCIM_TOKEN from .env SCIM_BEARER_TOKEN}"
CSV="${CSV:-${ROOT}/hr/demo-events.csv}"

# A sleeping Render instance holds the connection open while it boots instead of
# refusing it, so the first request just takes ~50s rather than failing fast.
# --max-time has to sit above that or curl hangs up before the app is listening.
WAKE_TIMEOUT=120
WAKE_ATTEMPTS=3

wake() {
  local name="$1"
  local url="$2"
  printf '%s' "Waking ${name} at ${url} ... "
  for attempt in $(seq 1 "${WAKE_ATTEMPTS}"); do
    if curl -sSf --max-time "${WAKE_TIMEOUT}" "${url}/health" >/dev/null 2>&1; then
      printf '%s\n' "ready"
      return 0
    fi
    printf '%s' "attempt ${attempt} failed, retrying "
  done
  printf '%s\n' "FAILED"
  echo "ERROR: ${name} never became healthy at ${url}/health" >&2
  echo "Check the Render dashboard — a suspended free service (out of monthly instance hours) looks the same as a slow one." >&2
  exit 1
}

echo "=== 1. Waking services (first request absorbs the cold start, ~1 min) ==="
wake "orchestrator" "${ORCH_URL}"
wake "SCIM server" "${SCIM_URL}"
echo

echo "=== 2. Replaying ${CSV} ==="
# Deliberately posting to the orchestrator's /hr/events rather than straight to
# SCIM: that path runs JML detection and birthright entitlement planning, and
# records audit events, so priming exercises the real pipeline instead of just
# stuffing rows into the target.
python3 "${ROOT}/scripts/import-hr-csv.py" "${CSV}" --url "${ORCH_URL}/hr/events"
echo

echo "=== 3. SCIM users after priming ==="
# Expected end state from the demo CSV: Alice active in Finance, Bob moved to
# Engineering, Carol deactivated with her roles stripped.
curl -sS -H "Authorization: Bearer ${SCIM_TOKEN}" \
  "${SCIM_URL}/scim/v2/Users" | python3 -m json.tool
echo

echo "Primed. The stack stays warm for 15 minutes after the last request."
