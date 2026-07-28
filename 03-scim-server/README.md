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

On fish: `source .venv/bin/activate.fish`.

- Health: [http://127.0.0.1:8001/health](http://127.0.0.1:8001/health)
- API docs: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)

Use port **8001** when running alongside the orchestrator on **8000**.

---

## Demo

```bash
export TOKEN="$(grep '^SCIM_BEARER_TOKEN=' .env | cut -d= -f2-)"
rm -f data/scim.db          # restart uvicorn after delete
./scripts/demo-scim.sh
```

On fish, set the token with `set -x TOKEN (grep '^SCIM_BEARER_TOKEN=' .env | cut -d= -f2-)`.

---

## Deploy — the store is disposable

On a Render **free** instance the filesystem is ephemeral and the service spins
down after 15 minutes idle, so `data/scim.db` is empty on every wake. I used this to simulate a daily sync/aggregation system, and its state is rebuilt from the source of record on demand.

The durable source of record is `hr/demo-events.csv` in Project 4, which lives
in git. To rebuild:

```bash
cd ../04-lifecycle-orchestrator
export ORCH_TOKEN="..." SCIM_TOKEN="..."
./scripts/prime-demo.sh
```

That wakes both services, replays the CSV through the orchestrator so JML
detection and entitlement planning actually run, and prints the resulting user
list. 

### Keeping it warm

Point a free scheduler such as cron-job.org at the unauthenticated `/health`
endpoint:

- **Once at the start of the window** — trigger the prime run. This request
absorbs the 50-60 second cold start, so the scheduler needs a generous
timeout (cron-job.org's free tier gives up at 30s, so run this one manually or
from a service that waits longer).
- **Every 14 minutes until the end of the window** — a plain `GET /health`,
beating the 15-minute idle timer.

Budget carefully. Render grants **750 free instance hours per month per
workspace**, shared across every free service, and spun-down services consume
none:


| Ping schedule         | Hours per month | Verdict                                                                                 |
| --------------------- | --------------- | --------------------------------------------------------------------------------------- |
| Every 14 min, 24/7    | ~730 of 750     | Starves the other free services; exhausting the pool suspends all of them until the 1st |
| Every 14 min, 10h/day | ~310 of 750     | Leaves headroom for the other three services                                            |


### Why the system wake/prime cannot be triggered from the Auth0 Action directly

Auth0 terminates an Action after **20 seconds** and the limit is not
configurable. A cold start is 50-60 seconds, so no retry or health check inside
the Action can outlast a sleeping server; Render holds the connection during
spin-up rather than refusing it, so the request is already waiting. Provisioning
from Auth0 therefore only works inside the warm window.

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
└── data/             # gitignored, and ephemeral on Render free
```

---

## SailPoint mapping


| This project     | SailPoint equivalent                  |
| ---------------- | ------------------------------------- |
| `/scim/v2/Users` | Target account API                    |
| Bearer token     | Application credential                |
| `externalId`     | Correlation ID (HR `employee_id`)     |
| `filter` lookup  | Connector search before create/update |


