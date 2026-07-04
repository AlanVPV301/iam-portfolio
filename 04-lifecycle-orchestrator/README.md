# Project 4 — Identity Lifecycle Orchestrator

Event-driven joiner / mover / leaver (JML) orchestration for a fictional HR source, with birthright entitlement planning and a full audit trail. Phase 1 builds the engine and persistence only — no Entra or SCIM connectors yet.

**Client:** FinFlow Ltd (same fictional fintech as Project 2)

**Stack:** Python 3.12, FastAPI, SQLite, YAML rules

---

## Phase 1 scope (current)

- Ingest HR records (API + CSV)
- Detect JOINER / MOVER / LEAVER by diffing authoritative state
- Compute provisioning plans from `rules/birthright.yaml` (stored, not executed)
- Append-only audit log + idempotent job processing
- Admin API to inspect persons, jobs, and audit events

**Not in Phase 1:** Entra Graph, SCIM targets, retry queues.

---

## Quick start

```bash
cd 04-lifecycle-orchestrator
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn orchestrator.main:app --reload
```

Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

Interactive API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Demo scripts

With the API running (`uvicorn orchestrator.main:app --reload`):

```bash
# Option A — curl walkthrough (JOINER → MOVER → LEAVER → idempotent replay)
chmod +x scripts/simulate-event.sh
rm -f data/orchestrator.db   # optional fresh start
./scripts/simulate-event.sh

# Option B — import ordered events from CSV
pip install -r requirements.txt
python3 scripts/import-hr-csv.py hr/demo-events.csv
```

**CSV files**

| File | Purpose |
|---|---|
| `hr/demo-events.csv` | Ordered lifecycle events (join / move / term) |
| `hr/employees.csv` | Reference roster snapshot (no `event_id`) |

---

```
04-lifecycle-orchestrator/
├── hr/                    # Sample HR feed (CSV)
├── rules/                 # Birthright entitlement maps
├── orchestrator/          # FastAPI app + engine (Phase 1+)
└── scripts/               # Demo / import helpers
```

---

## SailPoint mapping

| This project        | SailPoint equivalent        |
| ------------------- | --------------------------- |
| HR CSV / API        | Authoritative source        |
| `persons` table     | Identity profile            |
| JML detection       | Lifecycle events            |
| `birthright.yaml`   | Provisioning policy         |
| `plan_json` on jobs | Policy / provisioning plan  |
| `audit_events`      | Audit trail                 |
