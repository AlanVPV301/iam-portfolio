# Project 6 — WebAuthn Passkeys Lab

Passkey registration and authentication implemented directly against the WebAuthn API — no hosted IdP. Acts as the Relying Party for FinFlow Ltd, issuing its own signed session cookie after a successful assertion.

**Client:** FinFlow Ltd · **Stack:** Python 3.12, FastAPI, SQLite, py_webauthn

**Live:** [https://passkeys.alanvpv.dev](https://passkeys.alanvpv.dev)

---

## Endpoints scope

- `GET /health` — unauthenticated sanity check
- `GET /` — lab UI (shows the active RP ID and origin)
- `POST /webauthn/register/options` — creates the user if new, returns creation options
- `POST /webauthn/register/verify` — verifies attestation, stores credential + sign count
- `POST /webauthn/login/options` — returns request options scoped to the user's credentials
- `POST /webauthn/login/verify` — verifies assertion, updates sign count, issues a session
- `POST /logout` — clears current session
- `GET /me` — returns the current session, or 401 when unauthenticated

**Next:** Android Digital Asset Links (`assetlinks.json`)

---



## Scenarios

Simulated common success/failure scenarios in passkey configurations:

- `happy:` Correctly configured path
- `wrong_rp_id:` Simulates attempting the request using a Relying Party ID that does not match the expected one
- `wrong_origin:` Login/Register Verify uses a fake `expected_origin` → py_webauthn 400.
- `expired_challenge:` Simulates an expired or invalid cookie on pop_challenge -> 400
- `require_attestation:` Register options ask `attestation: direct`; verify rejects `fmt: none`. Register-only — synced passkeys such as Google PM and Apple Keychain fail, a packed/TPM key would pass (For example, a YubiKey).

The scenario is stored in the `_webauthn_tx` cookie, which resolves the RP_ID and Origin based on it to prevent the scenario to be changed mid-ceremony

## Quick start

```bash
cd 06-passkeys-webauthn-lab
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # set SESSION_SECRET
uvicorn passkeys.main:app --reload --port 8002
```

On fish: `source .venv/bin/activate.fish`.

- App: [http://localhost:8002](http://localhost:8002)
- Health: [http://localhost:8002/health](http://localhost:8002/health)
- API docs: [http://localhost:8002/docs](http://localhost:8002/docs)

`RP_ID` and `ORIGIN` must match the URL in the address bar exactly, or the browser refuses the ceremony. `ORIGIN` is read at import, so restart uvicorn after changing it.

Passkeys in this lab require user verification (PIN or biometric) on both registration and sign-in.

---



## Cookies

Ephemeral session cookies rather than using a persistent DB setup. Two signed cookies, both `HttpOnly` and both derived from `SESSION_SECRET` with different salts:


| Cookie              | Lifetime | Purpose                                                           |
| ------------------- | -------- | ----------------------------------------------------------------- |
| `_webauthn_tx`      | 5 min    | Challenge + ceremony type for one in-flight registration or login |
| `_webauthn_session` | 8 h      | Authenticated identity after a verified assertion                 |


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


| This project                   | Enterprise equivalent                    |
| ------------------------------ | ---------------------------------------- |
| Registration ceremony          | Authenticator enrolment / Authenticator+ |
| Assertion verification         | Passwordless authentication journey step |
| Sign count check               | Cloned-authenticator detection           |
| `RP_ID` / origin binding       | Tenant domain and allowed origin config  |
| Session cookie after assertion | Session issued on journey completion     |


