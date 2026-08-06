# Project 7 — Cloudflare Access intranet (dummy)

Static “FinFlow Intranet” page for an **Entra → Cloudflare Zero Trust** SSO lab. Not a real app — only proves Access authentication.

**Intended URL:** `https://internal.alanvpv.dev` (or any subdomain you protect with Access)

**Case study (SAML / SCIM / failures):** `[docs/sso-cloudflare-access.md](../docs/sso-cloudflare-access.md)`

---

## 1. Deploy the page (Cloudflare Pages)

Best fit: same Cloudflare account as Zero Trust.

1. Cloudflare Dashboard → **Workers & Pages** → **Create** → **Pages** → **Connect to Git**
2. Select `iam-portfolio`
3. Build settings:
  - **Root directory:** `07-cf-access-intranet`
  - **Build command:** *(empty)*
  - **Build output directory:** `/` *(or leave default for static — often* `.`*)*
4. Deploy
5. **Custom domains** → add `internal.alanvpv.dev`
6. In DNS (same zone): Pages will add the CNAME, or create
  `internal` → `<project>.pages.dev` (proxied / orange cloud)

Local preview:

```bash
cd 07-cf-access-intranet
python3 -m http.server 5501
```

Open [http://127.0.0.1:5501](http://127.0.0.1:5501)

---



## 2. Put Access in front of it

Zero Trust → **Access** → **Applications** → **Add an application** → **Self-hosted**


| Field              | Example                |
| ------------------ | ---------------------- |
| Application name   | FinFlow Intranet       |
| Session duration   | 24 hours (lab)         |
| Application domain | `internal.alanvpv.dev` |
| Path               | `/` (entire site)      |


**Identity provider:** **Generic SAML** (Native Entra ID OIDC is an alternative)

**Policy:** Allow emails / groups from your lab tenant (e.g. `bob.engineering@…` or a security group). Action: **Allow**.

Save → visit `https://internal.alanvpv.dev` in a private window → Entra login → this page.

---



## 3. Signed-in identity on the page

After Access login, `[app.js](app.js)` calls:

```http
GET /cdn-cgi/access/get-identity
```

(with the `CF_Authorization` cookie) and fills **Signed in as**, **Display name**, **Groups**, and **IdP** on the page.

For Generic SAML, Entra group claims often land under `custom["http://schemas.microsoft.com/ws/2008/06/identity/claims/groups"]` rather than top-level `groups[]`. The page reads both. Cloudflare IdP **SAML attributes** must include that claim URI (plus givenname/surname if you want a real display name).

This only works when the hostname is protected by Access (e.g. `https://internal.alanvpv.dev`). Local `python3 -m http.server` or a bare `*.pages.dev` URL without the same Access app will show “Could not load identity (open via Access)” — expected.

---

