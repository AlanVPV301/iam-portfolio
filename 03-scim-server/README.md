# Project 3 — SCIM 2.0 Provisioning Endpoint

Inbound SCIM 2.0 server for FinFlow Ltd custom apps. Bearer-authenticated REST API for user provisioning.

**Client:** FinFlow Ltd · **Stack:** Python 3.12, FastAPI, SQLite

---

## Scope

- `GET /health` — unauthenticated sanity check
- `GET /scim/v2/ServiceProviderConfig` — discovery
- `POST /scim/v2/Users` — create (server assigns `id` + `meta`)
- `GET /scim/v2/Users/{id}` — read by SCIM id
- `GET /scim/v2/Users?filter=...` — Entra-style lookup (`userName`, `externalId`)
- `PATCH /scim/v2/Users/{id}` — PatchOp (`replace` on `active`, `name`, `userName`, `roles`)

**Consumed by:** [Project 4 orchestrator](../04-lifecycle-orchestrator/) SCIM connector (`:8000` → `:8001`).

**Next:** Entra enterprise app provisioning (optional), `emails` PATCH support.

---

## Quick start

```bash
cd 03-scim-server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn scim.main:app --reload --port 8001
```

- Health: http://127.0.0.1:8001/health
- API docs: http://127.0.0.1:8001/docs

Use port **8001** when running alongside the orchestrator on **8000**.

---

## Demo

```bash
export TOKEN="$(grep '^SCIM_BEARER_TOKEN=' .env | cut -d= -f2-)"
rm -f data/scim.db          # restart uvicorn after delete
./scripts/demo-scim.sh
```

---

## Layout

```
03-scim-server/
├── scim/
│   ├── main.py
│   ├── models.py
│   ├── db.py
│   ├── patch.py
│   └── filter.py
├── scripts/demo-scim.sh
└── data/             # gitignored
```

---

## SailPoint mapping

| This project | SailPoint equivalent |
|---|---|
| `/scim/v2/Users` | Target account API |
| Bearer token | Application credential |
| `externalId` | Correlation ID (HR `employee_id`) |
| `filter` lookup | Connector search before create/update |
