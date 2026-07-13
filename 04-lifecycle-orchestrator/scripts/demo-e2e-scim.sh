#!/usr/bin/env bash
# FinFlow end-to-end: orchestrator (JML + lock) → SCIM provisioning
#
# Prerequisites (two terminals):
#   cd 03-scim-server && uvicorn scim.main:app --port 8001 --reload
#   cd 04-lifecycle-orchestrator && uvicorn orchestrator.main:app --port 8000 --reload
#
# Same SCIM_BEARER_TOKEN in both .env files.
#
# Usage:
#   ./scripts/demo-e2e-scim.sh           # keep existing DBs
#   ./scripts/demo-e2e-scim.sh --fresh   # wipe orchestrator + SCIM SQLite first

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCIM_ROOT="$(cd "${ROOT}/../03-scim-server" && pwd)"

ORCH_URL="${ORCH_URL:-http://127.0.0.1:8000}"
SCIM_URL="${SCIM_URL:-http://127.0.0.1:8001}"

require_health() {
  local name="$1"
  local url="$2"
  if ! curl -sf "${url}/health" >/dev/null; then
    echo "ERROR: ${name} not reachable at ${url}/health" >&2
    echo "Start both servers before running this script." >&2
    exit 1
  fi
}

if [[ "${1:-}" == "--fresh" ]]; then
  echo "=== Fresh start — removing SQLite databases ==="
  rm -f "${ROOT}/data/orchestrator.db" "${SCIM_ROOT}/data/scim.db"
  echo "(Servers can stay running — schema is recreated on next request.)"
  echo
fi

echo "=== Preflight: both APIs must be up ==="
require_health "Orchestrator" "${ORCH_URL}"
require_health "SCIM server" "${SCIM_URL}"
curl -sS "${ORCH_URL}/health" | python3 -m json.tool
curl -sS "${SCIM_URL}/health" | python3 -m json.tool
echo

echo "=== Orchestrator lifecycle demo (HR → plan → SCIM) ==="
BASE_URL="${ORCH_URL}" "${ROOT}/scripts/simulate-event.sh"

echo "=== SCIM SQLite — users provisioned by orchestrator ==="
SCIM_DB="${SCIM_ROOT}/data/scim.db"
if [[ ! -f "${SCIM_DB}" ]]; then
  echo "No SCIM database at ${SCIM_DB} (no users created yet?)" >&2
  exit 1
fi
sqlite3 "${SCIM_DB}" "SELECT external_id, user_name, active, roles_json FROM users ORDER BY external_id;"

echo
echo "=== Done. Orchestrator audit should include scim_provisioned / scim_skipped ==="
