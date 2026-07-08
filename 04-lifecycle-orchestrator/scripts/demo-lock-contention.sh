#!/usr/bin/env bash
# Per-identity lock demo only: concurrent events for same employee_id → 409, then retry.
#
# Prerequisites:
#   uvicorn orchestrator.main:app --reload
#
# Usage:
#   rm -f data/orchestrator.db && uvicorn orchestrator.main:app --reload   # fresh DB
#   ./scripts/demo-lock-contention.sh
#
# Or after simulate-event.sh (Alice already exists — evt-lock-a will be NOOP/MOVER, lock still applies)

set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
API="${BASE_URL}/hr/events"

echo "=== 1. Background request (holds lock ~5s) ==="
curl -sS -X POST "${API}" \
  -H "Content-Type: application/json" \
  -d '{
  "event_id": "evt-lock-a",
  "employee_id": "E001",
  "email": "alice.finance@finflow.example",
  "first_name": "Alice",
  "last_name": "Finance",
  "department": "Finance",
  "job_title": "Analyst",
  "status": "active"
}' | python3 -m json.tool &
BG_PID=$!

sleep 0.5

echo
echo "=== 2. Concurrent request (expect HTTP 409 + Retry-After: 5) ==="
LOCK_RESPONSE=$(curl -i -sS -X POST "${API}" \
  -H "Content-Type: application/json" \
  -d '{
  "event_id": "evt-lock-b",
  "employee_id": "E001",
  "email": "alice.finance@finflow.example",
  "first_name": "Alice",
  "last_name": "Finance",
  "department": "Finance",
  "job_title": "Analyst",
  "status": "active"
}')
echo "${LOCK_RESPONSE}"
if echo "${LOCK_RESPONSE}" | head -1 | grep -q "409"; then
  echo "(ok — identity locked as expected)"
else
  echo "(unexpected — wanted HTTP 409)" >&2
fi
echo

wait "${BG_PID}"

echo "=== 3. Retry rejected event (expect 201) ==="
curl -sS -X POST "${API}" \
  -H "Content-Type: application/json" \
  -d '{
  "event_id": "evt-lock-b",
  "employee_id": "E001",
  "email": "alice.finance@finflow.example",
  "first_name": "Alice",
  "last_name": "Finance",
  "department": "Finance",
  "job_title": "Analyst",
  "status": "active"
}' | python3 -m json.tool
