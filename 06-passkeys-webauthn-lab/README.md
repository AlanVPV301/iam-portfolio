# Project 6 — WebAuthn Passkeys Lab

Passkey registration and authentication implemented directly against the WebAuthn API — no hosted IdP. Acts as the Relying Party for FinFlow Ltd, issuing its own signed session cookie after a successful assertion.

**Client:** FinFlow Ltd · **Stack:** Python 3.12, FastAPI, SQLite, py_webauthn

**Live:** https://passkeys.alanvpv.dev

---

## Scope

- `GET /health` — unauthenticated sanity check
- `GET /` — lab UI (shows the active RP ID and origin)
- `POST /webauthn/register/options` — creates the user if new, returns creation options
- `POST /webauthn/register/verify` — verifies attestation, stores credential + sign count
- `POST /webauthn/login/options` — returns request options scoped to the user's credentials
- `POST /webauthn/login/verify` — verifies assertion, updates sign count, issues a session
- `GET /me` — returns the current session, or 401 when unauthenticated

**Next:** `POST /logout`, Android Digital Asset Links (`assetlinks.json`), failure scenarios (`SCENARIO` env var is documented but not yet wired up).

---

## Quick start

```bash
cd 06-passkeys-webauthn-lab
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # set SESSION_SECRET
uvicorn passkeys.main:app --reload --port 8002
```

On fish: `source .venv/bin/activate.fish`.

- App: http://localhost:8002
- Health: http://localhost:8002/health
- API docs: http://localhost:8002/docs

`RP_ID` and `ORIGIN` must match the URL in the address bar exactly, or the browser refuses the ceremony. `ORIGIN` is read at import, so restart uvicorn after changing it.

---

## Cookies

Two signed cookies, both `HttpOnly` and both derived from `SESSION_SECRET` with different salts:

| Cookie | Lifetime | Purpose |
|---|---|---|
| `_webauthn_tx` | 5 min | Challenge + ceremony type for one in-flight registration or login |
| `_webauthn_session` | 8 h | Authenticated identity after a verified assertion |

`Secure` is set automatically when `ORIGIN` starts with `https://`, so cookies work over local HTTP and stay strict in production.

---

## Deploy

Render web service behind a Cloudflare DNS record for `passkeys.alanvpv.dev`:

```env
RP_ID=alanvpv.dev
ORIGIN=https://passkeys.alanvpv.dev
SESSION_SECRET=<openssl rand -hex 32>
```

Registered passkeys live in SQLite, which resets on redeploy unless a persistent disk is attached — expected for a lab.

---

## Layout

```
06-passkeys-webauthn-lab/
├── passkeys/
│   ├── main.py              # routes
│   ├── webauthn_helpers.py  # py_webauthn wrappers, RP config
│   ├── sessions.py          # signed challenge + session cookies
│   └── db.py
├── static/
│   ├── registration.js
│   └── login.js
├── templates/index.html
└── data/                    # gitignored
```

---

## Transmit / SailPoint mapping

| This project | Enterprise equivalent |
|---|---|
| Registration ceremony | Authenticator enrolment / Authenticator+ |
| Assertion verification | Passwordless authentication journey step |
| Sign count check | Cloned-authenticator detection |
| `RP_ID` / origin binding | Tenant domain and allowed origin config |
| Session cookie after assertion | Session issued on journey completion |
