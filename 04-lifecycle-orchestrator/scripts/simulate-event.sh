#!/usr/bin/env bash
# FinFlow lifecycle demo: JOINER → MOVER → LEAVER → idempotent replay → lock contention
#
# Prerequisites:
#   uvicorn orchestrator.main:app --reload
#
# Usage (fresh DB recommended: rm -f data/orchestrator.db):
#   ./scripts/simulate-event.sh
#
# Lock-only quick demo (no JML walkthrough):
#   ./scripts/demo-lock-contention.sh

set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
API="${BASE_URL}/hr/events"

post_event() {
  local label="$1"
  local json="$2"
  echo "=== ${label} ==="
  curl -sS -X POST "${API}" \
    -H "Content-Type: application/json" \
    -d "${json}" | python3 -m json.tool
  echo
}

echo "Health check:"
curl -sS "${BASE_URL}/health" | python3 -m json.tool
echo

post_event "1. JOINER — Alice hired into Finance" '{
  "event_id": "evt-sim-001-alice-join",
  "employee_id": "E001",
  "email": "alice.finance@finflow.example",
  "first_name": "Alice",
  "last_name": "Finance",
  "department": "Finance",
  "job_title": "Analyst",
  "status": "active"
}'

post_event "2. JOINER — Bob hired into Finance" '{
  "event_id": "evt-sim-002-bob-join",
  "employee_id": "E002",
  "email": "bob.engineering@finflow.example",
  "first_name": "Bob",
  "last_name": "Engineering",
  "department": "Finance",
  "job_title": "Developer",
  "status": "active"
}'

post_event "3. MOVER — Bob Finance → Engineering" '{
  "event_id": "evt-sim-003-bob-move",
  "employee_id": "E002",
  "email": "bob.engineering@finflow.example",
  "first_name": "Bob",
  "last_name": "Engineering",
  "department": "Engineering",
  "job_title": "Developer",
  "status": "active"
}'

post_event "4. JOINER — Carol hired into ITAdmin" '{
  "event_id": "evt-sim-004-carol-join",
  "employee_id": "E003",
  "email": "carol.itadmin@finflow.example",
  "first_name": "Carol",
  "last_name": "ITAdmin",
  "department": "ITAdmin",
  "job_title": "Admin",
  "status": "active"
}'

post_event "5. LEAVER — Carol terminated" '{
  "event_id": "evt-sim-005-carol-term",
  "employee_id": "E003",
  "email": "carol.itadmin@finflow.example",
  "first_name": "Carol",
  "last_name": "ITAdmin",
  "department": "ITAdmin",
  "job_title": "Admin",
  "status": "terminated"
}'

post_event "6. Idempotent replay — same event_id as step 1" '{
  "event_id": "evt-sim-001-alice-join",
  "employee_id": "E001",
  "email": "alice.finance@finflow.example",
  "first_name": "Alice",
  "last_name": "Finance",
  "department": "Finance",
  "job_title": "Analyst",
  "status": "active"
}'

echo "=== 7. Lock — background Bob event (holds lock ~5s) ==="
curl -sS -X POST "${API}" \
  -H "Content-Type: application/json" \
  -d '{
  "event_id": "evt-sim-007-bob-lock-a",
  "employee_id": "E002",
  "email": "bob.engineering@finflow.example",
  "first_name": "Bob",
  "last_name": "Engineering",
  "department": "Engineering",
  "job_title": "Senior Developer",
  "status": "active"
}' | python3 -m json.tool &
LOCK_BG_PID=$!

sleep 0.5

echo
echo "=== 8. Lock — concurrent Bob event (expect 409 + Retry-After: 5) ==="
curl -i -sS -X POST "${API}" \
  -H "Content-Type: application/json" \
  -d '{
  "event_id": "evt-sim-008-bob-lock-b",
  "employee_id": "E002",
  "email": "bob.engineering@finflow.example",
  "first_name": "Bob",
  "last_name": "Engineering",
  "department": "Engineering",
  "job_title": "Senior Developer",
  "status": "active"
}'
echo

wait "${LOCK_BG_PID}"

echo "=== 9. Lock — retry rejected event (expect 201) ==="
curl -sS -X POST "${API}" \
  -H "Content-Type: application/json" \
  -d '{
  "event_id": "evt-sim-008-bob-lock-b",
  "employee_id": "E002",
  "email": "bob.engineering@finflow.example",
  "first_name": "Bob",
  "last_name": "Engineering",
  "department": "Engineering",
  "job_title": "Senior Developer",
  "status": "active"
}' | python3 -m json.tool
echo

echo "=== GET /persons ==="
curl -sS "${BASE_URL}/persons" | python3 -m json.tool
echo

echo "=== GET /hr_events ==="
curl -sS "${BASE_URL}/hr_events" | python3 -m json.tool
echo

echo "=== GET /audit_events ==="
curl -sS "${BASE_URL}/audit_events" | python3 -m json.tool
