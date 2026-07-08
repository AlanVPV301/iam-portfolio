#!/usr/bin/env bash
# FinFlow SCIM demo: create → filter → GET → PATCH → deactivate
#
# Prerequisites:
#   uvicorn scim.main:app --reload
#   export TOKEN="$(grep '^SCIM_BEARER_TOKEN=' .env | cut -d= -f2-)"
#
# Usage (fresh DB optional: rm -f data/scim.db):
#   ./scripts/demo-scim.sh

set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
SCIM="${BASE_URL}/scim/v2"
AUTH=(-H "Authorization: Bearer ${TOKEN:?Set TOKEN from .env SCIM_BEARER_TOKEN}")

post_json() {
  local label="$1"
  local url="$2"
  local data="$3"
  echo "=== ${label} ==="
  curl -sS -X POST "${url}" \
    "${AUTH[@]}" \
    -H "Content-Type: application/json" \
    -d "${data}" | python3 -m json.tool
  echo
}

patch_json() {
  local label="$1"
  local url="$2"
  local data="$3"
  echo "=== ${label} ==="
  curl -sS -X PATCH "${url}" \
    "${AUTH[@]}" \
    -H "Content-Type: application/json" \
    -d "${data}" | python3 -m json.tool
  echo
}

echo "=== Health ==="
curl -sS "${BASE_URL}/health" | python3 -m json.tool
echo

echo "=== ServiceProviderConfig ==="
curl -sS "${SCIM}/ServiceProviderConfig" "${AUTH[@]}" | python3 -m json.tool
echo

echo "=== POST /Users — create Alice ==="
CREATE_RESPONSE=$(curl -sS -X POST "${SCIM}/Users" \
  "${AUTH[@]}" \
  -H "Content-Type: application/json" \
  -d '{
    "userName": "alice.finance@finflow.example",
    "externalId": "E001",
    "name": { "givenName": "Alice", "familyName": "Finance" },
    "emails": [{ "value": "alice.finance@finflow.example", "primary": true }],
    "active": true
  }')
echo "${CREATE_RESPONSE}" | python3 -m json.tool
echo

USER_ID=$(echo "${CREATE_RESPONSE}" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

echo "=== GET /Users?filter=userName eq ... ==="
curl -sS -G "${SCIM}/Users" \
  "${AUTH[@]}" \
  --data-urlencode 'filter=userName eq "alice.finance@finflow.example"' | python3 -m json.tool
echo

echo "=== GET /Users/${USER_ID} ==="
curl -sS "${SCIM}/Users/${USER_ID}" "${AUTH[@]}" | python3 -m json.tool
echo

patch_json "PATCH — rename familyName to Smith" "${SCIM}/Users/${USER_ID}" '{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
  "Operations": [
    { "op": "replace", "path": "name.familyName", "value": "Smith" }
  ]
}'

echo "=== GET /Users?filter=externalId eq E001 ==="
curl -sS -G "${SCIM}/Users" \
  "${AUTH[@]}" \
  --data-urlencode 'filter=externalId eq "E001"' | python3 -m json.tool
echo

patch_json "PATCH — deactivate (LEAVER)" "${SCIM}/Users/${USER_ID}" '{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
  "Operations": [
    { "op": "replace", "path": "active", "value": false }
  ]
}'

echo "=== SQLite check ==="
sqlite3 data/scim.db "SELECT id, external_id, user_name, family_name, active FROM users;"
