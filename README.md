# IAM Engineering Portfolio

I'm a Tier 3 IAM support engineer with hands-on experience across Transmit Security, SailPoint, and Microsoft Entra ID — working tickets, escalations, incidents, and at the same time working on refining my implementation knowledge depth and experience.

This portfolio is meant to narrow the gap between my support experience and building identity and authentication integrations from scratch. Each project has working code and a write-up explaining the design and implementation.

The work here is done with the help of Cursor/Claude, official product and industry documentation, as well as some trial and error to get everything working as intended.

---



**Live hub:** [alanvpv.dev](https://alanvpv.dev) — static landing page in [`00-hub/`](./00-hub/).

**Case studies:** [SSO App Catalog](https://alanvpv.dev/sso/) · [Entra → AWS IAM Identity Center](./docs/sso-aws-iam-identity-center.md) · [Entra → Cloudflare Access](./docs/sso-cloudflare-access.md) · [Entra → Grafana Cloud (OIDC)](./docs/sso-grafana-oidc.md)

## Projects


| #   | Project                                                                 | Stack                                | Status     |
| --- | ----------------------------------------------------------------------- | ------------------------------------ | ---------- |
| 0   | [Portfolio hub](./00-hub/)                                              | HTML, CSS                            | ✅ Complete |
| 1   | [OIDC / OAuth 2.0 Authorization Code + PKCE Flow](./01-oidc-auth-flow/) | Python, Flask, Entra ID              | ✅ Complete |
| 2   | [Entra ID Conditional Access & PIM Implementation](./02-entra-ca-pim/)  | Entra ID, Microsoft Graph, Terraform | ✅ Complete |
| 3   | [SCIM 2.0 Provisioning Endpoint](./03-scim-server/)                     | Python, FastAPI, SQLite              | ✅ Complete |
| 4   | [Identity Lifecycle Orchestrator](./04-lifecycle-orchestrator/)         | Python, FastAPI, SQLite              | ✅ Complete |
| 5   | [Auth0 Adaptive MFA & Step-Up (FinFlow)](./05-auth0-app/)               | Python, Flask, Auth0                 | ✅ Complete |
| 6   | [WebAuthn Passkeys & Digital Asset Links Lab](./06-passkeys-webauthn-lab/) | Python, FastAPI, SQLite, WebAuthn | 🔵 In progress |


---



## Running the projects

Each project has its own virtualenv and `.env` — see the per-project README. Commands are written in bash syntax; on fish, two of them differ:

| bash | fish |
| --- | --- |
| `source .venv/bin/activate` | `source .venv/bin/activate.fish` |
| `export TOKEN="value"` | `set -x TOKEN "value"` |

Demo scripts under each `scripts/` directory have a bash shebang, so `./scripts/demo-*.sh` runs unchanged from any shell.


---



## Background

**Current role:** Tier 3 IAM Support Engineer. Previously Cloud Support Engineer 3 At SailPoint.

**What I work with daily/have experience with:**

- OAuth 2.0 / OIDC — deep troubleshooting across multiple IdPs and SDK implementations
- SAML / SSO / federation — SME-level from Atlassian, SailPoint, and Transmit Security
- SailPoint ISC — lifecycle management, provisioning, access reviews, virtual appliances
- Fraud detection / risk-based auth — DRS at Transmit Security
- Observability — Grafana, Coralogix, Cloudflare, OpenSearch, Splunk

**What this portfolio builds:**

- Writing auth flows in code, not just configuring them
- SCIM protocol from the server side
- Microsoft Entra ID hands-on depth beyond troubleshooting
- Risk-based auth and step-up on a commercial IdP (Auth0)
- Identity architecture design thinking at architect level

