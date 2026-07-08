# Project 4 — Identity Lifecycle Orchestrator

Event-driven joiner / mover / leaver (JML) orchestration for a fictional HR source, with birthright entitlement planning and a full audit trail.

**Client:** FinFlow Ltd · **Stack:** Python 3.12, FastAPI, SQLite, YAML rules

---

## Scope

**Phase 1:** HR ingest, JML detection, birthright plans (stored, not executed), audit log, idempotent `event_id` replay.

**Phase 1.5:** Per-employee in-memory lock (~5s simulated provisioning). Concurrent events for the same `employee_id` get `409 Conflict` + `Retry-After: 5`.

**Not yet:** Entra Graph, SCIM targets, durable queues.

---

## Quick start

```bash
cd 04-lifecycle-orchestrator
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn orchestrator.main:app --reload
```

- Health: http://127.0.0.1:8000/health
- API docs: http://127.0.0.1:8000/docs

---

## Demo scripts

With the API running:

```bash
rm -f data/orchestrator.db   # optional fresh start

./scripts/simulate-event.sh           # JML + idempotent replay + lock contention (steps 7–9)
./scripts/demo-lock-contention.sh     # lock-only quick demo (409 + retry)
python3 scripts/import-hr-csv.py hr/demo-events.csv
```

| Script | Purpose |
|---|---|
| `simulate-event.sh` | JOINER → MOVER → LEAVER → replay → **lock 409** |
| `demo-lock-contention.sh` | Lock-only: two concurrent curls for `E001` |
| `import-hr-csv.py` | POST rows from `hr/demo-events.csv` |

---

## SailPoint mapping

| This project | SailPoint equivalent |
|---|---|
| HR CSV / API | Authoritative source |
| `persons` | Identity profile |
| JML detection | Lifecycle events |
| `birthright.yaml` | Provisioning policy |
| `plan_json` on `hr_events` | Provisioning plan |
| `audit_events` | Audit trail |
| Per-employee lock | Identity processing mutex |
