# Portfolio hub

Static landing page for `alanvpv.dev` — name, title, LinkedIn, and links into the live demos.

## Local preview

```bash
cd 00-hub
python3 -m http.server 5500
```

Open http://127.0.0.1:5500

## Deploy (Render static site)

1. New → **Static Site**, same `iam-portfolio` repo
2. **Root Directory:** `00-hub`
3. **Build Command:** leave empty (or `true`)
4. **Publish Directory:** `.`
5. Add custom domain `alanvpv.dev` (and optionally `www`) in Cloudflare as a CNAME to the `onrender.com` host — DNS only until the cert issues, SSL mode **Full**

No environment variables required.

## Links

| Button | Destination |
| --- | --- |
| Passkeys / WebAuthn | https://passkeys.alanvpv.dev |
| Auth0 Adaptive MFA | https://auth0.alanvpv.dev |
| OIDC + PKCE (Entra) | https://oidc.alanvpv.dev |
| Lifecycle Orchestrator | https://jml.alanvpv.dev/docs |
| SCIM 2.0 Server | https://scim.alanvpv.dev/docs |
| Entra CA & PIM | GitHub tree (no live service) |
| SSO App Catalog | `/sso/` — Entra integrations table + architecture |
