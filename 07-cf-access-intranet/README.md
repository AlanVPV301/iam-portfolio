# Project 7 — Cloudflare Access intranet (dummy)

Static “FinFlow Intranet” page for an **Entra → Cloudflare Zero Trust** SSO lab. Not a real app — only proves Access authentication.

**Intended URL:** `https://internal.alanvpv.dev` (or any subdomain you protect with Access)

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


**Identity provider:** Entra ID (OIDC gallery connector is fine; use **Generic SAML** if you need a pure SAML story for the SSO catalog).

**Policy:** Allow emails / groups from your lab tenant (e.g. `bob.engineering@…` or a security group). Action: **Allow**.

Save → visit `https://internal.alanvpv.dev` in a private window → Entra login → this page.

---

