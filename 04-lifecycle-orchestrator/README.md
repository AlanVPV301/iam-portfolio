# Project 4 — Identity Lifecycle Orchestrator

Event-driven joiner / mover / leaver (JML) orchestration for a fictional HR source, with birthright entitlement planning, SCIM provisioning, and a full audit trail.

**Client:** FinFlow Ltd · **Stack:** Python 3.12, FastAPI, SQLite, YAML rules

---

## Scope

**Phase 1:** HR ingest, JML detection, birthright plans, audit log, idempotent `event_id` replay.

**Phase 1.5:** Per-employee in-memory lock (~5s simulated provisioning). Concurrent events for the same `employee_id` get `409 Conflict` + `Retry-After: 5`.

**Phase 2b (current):** Outbound SCIM connector → [Project 3](../03-scim-server/) (`POST` / `GET filter` / `PATCH`). Audit: `scim_provisioned`, `scim_skipped`.

**Not yet:** Entra Graph (`entra_groups`), durable queues, Entra → SCIM direct provisioning.

---

## Quick start

```bash
cd 04-lifecycle-orchestrator
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set SCIM_BEARER_TOKEN (match 03-scim-server)
uvicorn orchestrator.main:app --reload
```

- Health: http://127.0.0.1:8000/health
- API docs: http://127.0.0.1:8000/docs

---

## End-to-end with SCIM (Project 3)

Use the **same** `SCIM_BEARER_TOKEN` in both `.env` files. Run on different ports:

```bash
# Terminal 1 — SCIM target
cd ../03-scim-server && source .venv/bin/activate
uvicorn scim.main:app --port 8001 --reload

# Terminal 2 — orchestrator
cd ../04-lifecycle-orchestrator && source .venv/bin/activate
uvicorn orchestrator.main:app --port 8000 --reload

# Terminal 3 — demo
./scripts/demo-e2e-scim.sh --fresh   # safe with servers already running
```

Or keep existing DBs: `./scripts/demo-e2e-scim.sh`

---

## Demo scripts

```bash
./scripts/demo-e2e-scim.sh --fresh      # orchestrator + SCIM e2e (both servers required)
./scripts/simulate-event.sh           # JML + replay + lock + SCIM provision
./scripts/demo-lock-contention.sh     # lock-only (409 + retry)
python3 scripts/import-hr-csv.py hr/demo-events.csv
```

| Script | Purpose |
|---|---|
| `demo-e2e-scim.sh` | Preflight both APIs, run full simulate-event, verify SCIM DB |
| `simulate-event.sh` | Full walkthrough including SCIM side effects |
| `demo-lock-contention.sh` | Per-identity lock demo only |
| `import-hr-csv.py` | POST rows from `hr/demo-events.csv` |

---

## Layout

```
04-lifecycle-orchestrator/
├── orchestrator/
│   ├── main.py
│   ├── engine.py
│   ├── connectors/scim.py   # outbound SCIM client
│   └── ...
├── rules/birthright.yaml
├── hr/
└── scripts/
```

---

## SailPoint mapping

| This project | SailPoint equivalent |
|---|---|
| HR CSV / API | Authoritative source |
| `persons` | Identity profile |
| JML detection | Lifecycle events |
| `birthright.yaml` | Provisioning policy |
| `connectors/scim.py` | SCIM provisioning connector |
| `audit_events` | Audit trail |
| Per-employee lock | Identity processing mutex |
