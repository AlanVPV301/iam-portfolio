# Project 1 — OIDC / OAuth 2.0 Authorization Code + PKCE Flow
A minimal Flask app implementing the full OIDC authorization code flow with PKCE
from scratch. No SDKs handle the auth logic — every step is explicit in the code.
**Stack:** Python 3.12, Flask, Microsoft Entra ID (M365 dev tenant)
---
## What it does
1. User clicks "Sign in with Microsoft"
2. App generates a PKCE `code_verifier` + `code_challenge` and redirects to Entra ID
3. User authenticates on Microsoft's login page
4. Entra ID redirects back with an authorization code
5. App exchanges the code (+ verifier) for tokens server-to-server
6. `id_token` claims are decoded and displayed
7. Session is established — `/profile` is a protected route requiring valid session
8. Token refresh runs silently when the access token expires
9. Logout clears the local session and the Entra ID SSO session
## Flow diagram
```mermaid
sequenceDiagram
    participant B as Browser
    participant F as Flask App
    participant E as Entra ID
    B->>F: GET /login
    F->>F: Generate code_verifier, code_challenge = SHA256(verifier)
    F->>F: Store verifier in signed session cookie
    F-->>B: 302 → Entra ID /authorize?code_challenge=...
    B->>E: GET /authorize (user logs in)
    E-->>B: 302 → /callback?code=...&state=...
    B->>F: GET /callback?code=...&state=...
    F->>F: Verify state matches session (CSRF check)
    F->>E: POST /token — code + code_verifier + client_secret
    E->>E: SHA256(verifier) == stored challenge?
    E-->>F: access_token, id_token, refresh_token
    F->>F: Decode id_token payload, store session
    F-->>B: Render claims / redirect to /profile
Design decisions
Why PKCE? What attack does it prevent?
PKCE (RFC 7636) prevents the authorization code interception attack. Without it, the authorization code is the only secret in the flow — if a malicious app on the same device intercepts it (via a rogue browser extension, custom URI scheme hijacking on mobile, or a compromised redirect), it can exchange the code for tokens independently.

PKCE binds the code to a one-time code_verifier that only the legitimate client knows. The verifier never travels over the network until the token exchange — Entra ID stores only its SHA-256 hash (the code_challenge). Intercepting the code is useless without also knowing the verifier.

Why S256 and not plain? The plain method sends the verifier as the challenge directly, so intercepting the /authorize request reveals it. S256 sends only the hash — the verifier stays secret until the token POST.

What's the difference between id_token and access_token?
id_token	access_token
Purpose
Authentication — who is this user?
Authorization — what can this bearer do?
Audience
Your application (aud = your client ID)
A resource server (an API)
Consumer
Your app validates and reads claims from it
Your app treats it as opaque and forwards it
Contains
User identity claims: sub, oid, name, email
Scopes, roles, permissions
Which one do you validate? The id_token. You verify its signature against the IdP's public keys (JWKS endpoint), check iss matches your tenant, check aud matches your client ID, and check exp hasn't passed. The access_token is validated by the API that receives it, not by your app.

Note: this app decodes the id_token payload without signature verification — acceptable for a local demo, not for production. See production notes below.

Why store the code_verifier in the session and not elsewhere?
The verifier must survive the browser round-trip to Entra ID and back, but must never travel over the network (that defeats PKCE). A server-signed Flask session cookie is the right transport: it stays in the browser, is tamper-evident (signed with SECRET_KEY), and is never visible in the URL.

What if you stored it client-side (e.g. localStorage)? A malicious script with XSS access to the page could read it. Combined with an intercepted authorization code, an attacker would have everything needed to complete the token exchange. Server-side storage (or a signed cookie) keeps the verifier out of reach of client-side scripts.

What I'd do differently in production
Issue	Demo approach	Production approach
Session storage
Signed cookie — JWTs bloat it past 4KB browser limit
Flask-Session + Redis — cookie holds only a session ID
Token signature validation
Not implemented
Fetch Entra ID JWKS, verify RS256 signature on every id_token
response_mode
query — code appears in URL and server logs
form_post — code sent in POST body, never in logs
Client secret
Loaded from .env
Loaded from a secrets manager (Azure Key Vault, AWS Secrets Manager)
HTTPS
HTTP localhost
TLS everywhere — cookies must be Secure flag in prod
Error handling
Bare string responses
Proper error pages, structured logging
How to run
# 1. Clone and enter the project
cd 01-oidc-auth-flow
# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate
# 3. Install dependencies
pip install -r requirements.txt
# 4. Configure environment
cp .env.example .env
# Edit .env with your Entra ID app registration values
# 5. Run
cd app && python3 app.py
Open http://localhost:5000 and click "Sign in with Microsoft".

Entra ID app registration requirements:

Redirect URI: http://localhost:5000/callback (Web platform)
Supported account types: single tenant
A client secret under Certificates & secrets