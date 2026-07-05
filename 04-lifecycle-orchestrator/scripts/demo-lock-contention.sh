#!/usr/bin/env bash
# Per-identity lock demo: concurrent events for same employee_id → 409, then retry succeeds.
#
# Prerequisites:
#   uvicorn orchestrator.main:app --reload
#
# Usage (fresh DB recommended: rm -f data/orchestrator.db):
#   ./scripts/demo-lock-contention.sh

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
echo "=== 2. Concurrent request (expect 409 + Retry-After) ==="
curl -i -sS -X POST "${API}" \
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
}'
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
