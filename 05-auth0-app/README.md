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
┌─────────────┐   step_up / amr check   ┌──────────────┐   HTTPS SCIM  ┌─────────────┐
│ server.py   │                         │ post-user-   │ ────────────► │ Project 3   │
│ (Render)    │                         │ registration │               │ SCIM public │
└─────────────┘                         └──────────────┘               └─────────────┘
```

**Split of responsibility:** Flask decides *when* step-up is required; Auth0 Actions enforce MFA during login.

**Important:** Auth0 Actions run in Auth0’s cloud. They cannot reach `localhost`. For signup → SCIM, the Action must call a **public HTTPS** SCIM origin (e.g. Render at `https://scim.alanvpv.dev`). No Cloudflare Tunnel is required when SCIM is on Render.

---

## Quick start

### 1. Auth0 dashboard (one-time)

Create a **Regular Web App** named FinFlow. Set:

| Setting | Local | Production (Render) |
|---------|--------|---------------------|
| Allowed Callback URLs | `http://localhost:5000/callback` | `https://auth.alanvpv.dev/callback` |
| Allowed Logout URLs | `http://localhost:5000` | `https://auth.alanvpv.dev` |
| Allowed Web Origins | `http://localhost:5000` | `https://auth.alanvpv.dev` |

You can list both local and production URLs in the same Auth0 app.

Enable **MFA** (TOTP or email) and **Adaptive MFA / Risk Assessment**.

Copy Action code from `actions/` into Auth0 (see [Actions](#auth0-actions) below). Deploy the SCIM Action only after Project 3 is reachable at a public URL (or a temporary tunnel for local-only testing).

### 2. Flask app

```bash
cd 05-auth0-app
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill AUTH0_* and AUTH0_SECRET
python server.py
```

On fish: `source .venv/bin/activate.fish`.

- App: http://127.0.0.1:5000
- Generate secret: `openssl rand -hex 32`

### 3. SCIM (optional — for signup provisioning)

**Local lab (Flask only):**

```bash
cd ../03-scim-server
source .venv/bin/activate
uvicorn scim.main:app --port 8001 --reload
```

**Signup → SCIM via Auth0 Action:** deploy Project 3 publicly (Render + Cloudflare DNS), then set Action secrets (below). Local-only alternative: temporary tunnel to `:8001` and put that URL in `SCIM_URL`.

Use the same bearer token in SCIM `.env` (`SCIM_BEARER_TOKEN`) and the Action secret `BEARER`.

---

## Deploy (Cloudflare DNS + Render)

| Service | Public URL | Notes |
|---------|------------|--------|
| Flask app (this project) | `https://auth.alanvpv.dev` | `APP_BASE_URL`; CNAME → Render |
| SCIM (Project 3) | `https://scim.alanvpv.dev` | Action target; set `PUBLIC_BASE_URL` on SCIM |

1. Deploy SCIM on Render with custom domain; confirm `curl https://scim.alanvpv.dev/health`.
2. In the Post User Registration Action, set secrets `SCIM_URL=https://scim.alanvpv.dev` and `BEARER=<same as SCIM_BEARER_TOKEN>`; paste [`create-scim-user.js`](actions/create-scim-user.js); Deploy.
3. Deploy this Flask app; set `APP_BASE_URL=https://auth.alanvpv.dev` and Auth0 callback/logout/origins.
4. Signup a test user → SCIM user with `externalId` = `auth0|...`.

If SCIM is on Render **Free**, cold starts can cause Action timeouts during demos — prefer **Starter** for SCIM when showing signup provisioning.

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

**Action secrets** (Post User Registration):

| Secret | Value |
|--------|--------|
| `SCIM_URL` | Public SCIM origin, no trailing slash (e.g. `https://scim.alanvpv.dev`) |
| `BEARER` | Same as `SCIM_BEARER_TOKEN` in Project 3 |

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
