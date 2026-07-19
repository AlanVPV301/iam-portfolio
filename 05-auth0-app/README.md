# Project 5 — Auth0 Adaptive MFA & Step-Up (FinFlow)

Employee portal on **Auth0 Universal Login** with Post-login Actions for risk-based MFA, step-up on sensitive routes, and signup provisioning to the [Project 3 SCIM server](../03-scim-server/).

**Client:** FinFlow Ltd · **Stack:** Python 3.12, Flask, Auth0 Actions, auth0-server-python

---

## Scope

| Layer | What |
|-------|------|
| **Flask app** | Login, dashboard, `/payroll` step-up gate (`amr` check), `returnTo` cookie |
| **Post-login Action** | Adaptive MFA (new device) + forced MFA when `step_up=payroll` |
| **Post-user-registration Action** | Signup → GET/POST Project 3 SCIM (`externalId` = Auth0 `user_id`) |

**Not in scope:** Auth0 Organizations, FGA, Entra federation.

---

## Architecture

```text
┌─────────────┐     login/MFA      ┌──────────────┐     Actions (JS)    ┌─────────────┐
│   Browser   │ ◄────────────────► │    Auth0     │ ◄────────────────── │ Login flow  │
└──────┬──────┘                    └──────┬───────┘                     │ Registration│
       │                                  │                               └─────────────┘
       │ callback                         │ signup
       ▼                                  ▼
┌─────────────┐   step_up / amr check   ┌──────────────┐   SCIM HTTP   ┌─────────────┐
│ server.py   │                         │ post-user-   │ ────────────► │ Project 3   │
│ :5000       │                         │ registration │               │ SCIM :8001  │
└─────────────┘                         └──────────────┘               └─────────────┘
```

**Split of responsibility:** Flask decides *when* step-up is required; Auth0 Actions enforce MFA during login.

---

## Quick start

### 1. Auth0 dashboard (one-time)

Create a **Regular Web App** named FinFlow. Set:

| Setting | Value |
|---------|--------|
| Allowed Callback URLs | `http://localhost:5000/callback` |
| Allowed Logout URLs | `http://localhost:5000` |
| Allowed Web Origins | `http://localhost:5000` |

Enable **MFA** (TOTP or email) and **Adaptive MFA / Risk Assessment**.

Copy Action code from `actions/` into Auth0 (see [Actions](#auth0-actions) below).

### 2. Flask app

```bash
cd 05-auth0-app
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill AUTH0_* and AUTH0_SECRET
python server.py
```

- App: http://127.0.0.1:5000
- Generate secret: `openssl rand -hex 32`

### 3. SCIM (optional — for signup provisioning)

```bash
cd ../03-scim-server
source .venv/bin/activate
uvicorn scim.main:app --port 8001 --reload
```

Use the same bearer token in SCIM `.env` and the Action secret `BEARER`. For local Actions, expose SCIM via a tunnel and set `SCIM_URL` in the Action.

---

## Demo

```bash
# With app + SCIM running
./scripts/demo-auth0.sh
./scripts/demo-auth0.sh --scim   # print SCIM SQLite after manual signup
```

**Browser checklist:**

1. Login → dashboard (`MFA this session: False` on known device)
2. Incognito login → adaptive MFA challenge
3. **View Payroll** → step-up MFA → salary page
4. Signup → verify SCIM row: `external_id` = `auth0|...`

Check **Auth0 → Monitoring → Logs → Success Login → Action Details** for Action execution.

---

## Auth0 Actions

Mirror these in the dashboard; keep repo copies in sync.

| File | Trigger | Purpose |
|------|---------|---------|
| `actions/post-login-finflow.js` | **Login** | Adaptive MFA + `step_up` payroll |
| `actions/create-scim-user.js` | **Post User Registration** | Idempotent SCIM create |

**Post-login:** Actions → Flows → Login → drag Action between Start and Complete → Deploy.

**Registration:** Actions → Flows → Post User Registration → add `create-scim-user` → Deploy.

Action secrets: `BEARER` = same value as `SCIM_BEARER_TOKEN` in Project 3.

---

## Layout

```text
05-auth0-app/
├── server.py
├── templates/dashboard.html
├── actions/
│   ├── post-login-finflow.js
│   └── create-scim-user.js
├── scripts/demo-auth0.sh
└── .env.example
```

---

## SailPoint / Transmit mapping

| This project | Enterprise equivalent |
|--------------|----------------------|
| Post-login Action | Risk policy / step-up rule |
| `amr` check on `/payroll` | Application-level step-up |
| Signup → SCIM Action | IdP outbound provisioning |
| Adaptive MFA | DRS / RBA new-device signal |
