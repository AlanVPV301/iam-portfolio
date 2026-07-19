#!/usr/bin/env bash
# FinFlow Auth0 demo — preflight + manual walkthrough checklist
#
# Prerequisites:
#   Terminal 1: cd 03-scim-server && uvicorn scim.main:app --port 8001 --reload
#   Terminal 2: cd 05-auth0-app && python server.py
#   Auth0 Actions deployed (post-login + post-user-registration)
#   Tunnel or public URL for SCIM if testing signup → SCIM Action
#
# Usage:
#   ./scripts/demo-auth0.sh
#   ./scripts/demo-auth0.sh --scim   # also print SCIM users table

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCIM_ROOT="$(cd "${ROOT}/../03-scim-server" && pwd)"

APP_URL="${APP_URL:-http://127.0.0.1:5000}"
SCIM_URL="${SCIM_URL:-http://127.0.0.1:8001}"

require_health() {
  local name="$1"
  local url="$2"
  if ! curl -sf "${url}/health" >/dev/null; then
    echo "ERROR: ${name} not reachable at ${url}/health" >&2
    exit 1
  fi
}

echo "=== Preflight ==="
if curl -sf -o /dev/null "${APP_URL}/"; then
  echo "FinFlow app: OK (${APP_URL})"
else
  echo "ERROR: FinFlow app not reachable at ${APP_URL}" >&2
  exit 1
fi
echo

if curl -sf "${SCIM_URL}/health" >/dev/null 2>&1; then
  echo "SCIM server: OK (${SCIM_URL})"
  SCIM_UP=1
else
  echo "SCIM server: not running (optional unless testing signup → SCIM Action)"
  SCIM_UP=0
fi
echo

echo "=== Manual demo (browser) ==="
echo "1. Open ${APP_URL}"
echo "2. Login → dashboard shows name, email, MFA this session"
echo "3. Incognito login → expect adaptive MFA (Post-login Action)"
echo "4. Click View Payroll → step-up MFA → payroll page"
echo "5. Signup new user → post-user-registration Action → SCIM user row"
echo

if [[ "${1:-}" == "--scim" && "${SCIM_UP}" == "1" ]]; then
  echo "=== SCIM users ==="
  sqlite3 "${SCIM_ROOT}/data/scim.db" \
    "SELECT external_id, user_name, active FROM users ORDER BY external_id;" \
    2>/dev/null || echo "(no scim.db yet — sign up a user first)"
fi

echo "=== Auth0 logs ==="
echo "Monitoring → Logs → Success Login → Action Details (verify Actions ran)"
