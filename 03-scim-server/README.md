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
- `PATCH /scim/v2/Users/{id}` — PatchOp (`replace` on `active`, name, etc.)

**Next:** Entra provisioning hookup, orchestrator SCIM client (Project 4).

---

## Quick start

```bash
cd 03-scim-server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set SCIM_BEARER_TOKEN
uvicorn scim.main:app --reload
```

- Health: http://127.0.0.1:8000/health
- API docs: http://127.0.0.1:8000/docs

---

## Demo

```bash
export TOKEN="$(grep '^SCIM_BEARER_TOKEN=' .env | cut -d= -f2-)"
rm -f data/scim.db          # optional fresh start
./scripts/demo-scim.sh
```

---

## Layout

```
03-scim-server/
├── scim/
│   ├── main.py       # routes
│   ├── models.py     # SCIM User + PatchOp
│   ├── db.py         # SQLite
│   ├── patch.py      # apply PatchOp to row
│   └── filter.py     # parse filter=userName eq "..."
├── scripts/
│   └── demo-scim.sh
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
