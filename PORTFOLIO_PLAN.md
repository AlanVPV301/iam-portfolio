# IAM Engineering Portfolio Plan
> Alan Papazoglou · Tier 3 Support → IAM Engineer transition
> Last updated: June 2026

---

## Context & Goal

I'm a Tier 3 support engineer with deep hands-on experience in IAM, CIAM, OAuth 2.0, OIDC, SAML, SailPoint ISC, and Transmit Security's identity/fraud platform. My gap is **implementation depth** — I've configured and troubleshot these systems at scale, but haven't built them from scratch.

This portfolio manufactures evidence of that implementation depth through 6 projects, each with working code and a detailed write-up explaining design decisions (not just what I did, but why).

**Target roles:** IAM Engineer → Senior IAM Engineer → Identity Security Architect
**Target salary range:** $107K–$171K (mid) / $140K–$200K+ (senior/architect)

---

## Certification Roadmap

| Phase | Cert | Timeline | Why |
|---|---|---|---|
| 1 | **SC-300** — Microsoft Identity Administrator | Month 1–5 | Formalises existing Entra ID / OIDC / SAML knowledge. Most in-demand IAM cert in enterprise. |
| 2 | **SailPoint ISC Specialist** | Month 4–6 | You already have the foundation credential. Deepens existing SailPoint advantage. |
| 3 | **CIAM®** — Certified Identity & Access Manager | Month 7–9 | Vendor-neutral gold standard. Rare combo with SC-300 + SailPoint. |
| 4 | **SC-100** — Cybersecurity Architect Expert *(stretch)* | Month 10–12 | Requires SC-300 + one more associate cert (SC-200 or AZ-500). Opens architect/consulting track. |

### Study resources for SC-300
- Microsoft Learn SC-300 learning paths (free, hands-on): learn.microsoft.com
- M365 Developer tenant (free Entra ID P2 sandbox): developer.microsoft.com/microsoft-365/dev-program
- MeasureUp practice exams (paid, worth it close to exam date)

---

## Existing Strengths (don't undersell these)

- **SAML / SSO / federation** — SME-level from Atlassian + SailPoint + Transmit Security
- **OAuth 2.0 / OIDC** — deep troubleshooting across multiple IdPs and SDK implementations
- **Observability** — Grafana, Coralogix, Cloudflare, OpenSearch, Splunk. Rare in IAM engineers.
- **Fraud detection / risk-based auth** — DRS experience at Transmit Security is a premium specialisation
- **SailPoint ISC** — lifecycle management, provisioning, access reviews, virtual appliances
- **Cross-team collaboration** — engineering escalation, incident management, on-call

---

## Knowledge Gaps to Close

| Priority | Gap | How the portfolio closes it |
|---|---|---|
| 🔴 High | Writing auth flows in code (not just configuring them) | Project 1 |
| 🔴 High | SCIM protocol from the server side | Project 3 |
| 🔴 High | Microsoft Entra ID hands-on depth (PIM, CA, Governance) | Project 2 + SC-300 |
| 🟡 Medium | Identity architecture design thinking | Project 4 |
| 🟡 Medium | Workload / non-human identities | SC-300 domain + Okta NHI learning path |
| 🟡 Medium | IaC for identity (Terraform + Entra/Okta providers) | Extend Project 2 |

---

## The 6 Projects

---

### Project 1 · OIDC / OAuth 2.0 Authorization Code + PKCE Flow
**Status:** 🔵 In progress
**Folder:** `01-oidc-auth-flow/`
**Stack:** Python 3.12, Flask, Entra ID (M365 dev tenant)

#### What it demonstrates
Building the full OIDC authorization code + PKCE flow from scratch — no SDK handling the auth logic. Every step is explicit: PKCE generation, redirect construction, code exchange, token validation, refresh, and scope-based route protection.

#### Build stages
1. App registration in Entra ID + Flask skeleton that redirects to login
2. Callback handler: auth code → token exchange, display ID token claims
3. Token refresh, session management, protected routes

#### What the README must answer
- Why PKCE? What attack does it prevent?
- What happens to the code verifier if you store it client-side?
- What's the difference between `access_token` and `id_token` — and which one do you validate?
- What would I do differently in a production deployment?

#### Free resources
- MSAL Python reference (don't use it — read it): github.com/AzureAD/microsoft-authentication-library-for-python
- RFC 6749 (OAuth 2.0): tools.ietf.org/html/rfc6749
- RFC 7636 (PKCE): tools.ietf.org/html/rfc7636
- Auth0 "Authorization Code Flow with PKCE" explainer: auth0.com/docs/get-started/authentication-and-authorization-flow/authorization-code-flow-with-pkce

---

### Project 2 · Entra ID Conditional Access & PIM Implementation
**Status:** ⚪ Not started
**Folder:** `02-entra-ca-pim/`
**Stack:** Microsoft Entra ID (M365 dev tenant), Microsoft Graph API

#### What it demonstrates
Designing and implementing a full Conditional Access policy suite with PIM for a fictional mid-size company. Treated as a real client engagement — includes a written design doc, implementation, and rationale for every decision.

#### Fictional client brief
*FinFlow Ltd — 400-person fintech, hybrid workforce, Microsoft 365 E3, moving to zero trust. High-risk roles: Finance, Engineering, IT Admin.*

#### What to implement
- CA policies: MFA enforcement by role, compliant device requirement, location-based restrictions, sign-in risk policy
- PIM: Global Admin, Security Admin, Privileged Role Admin — all requiring approval + justification
- Identity Secure Score baseline + improvement plan
- MFA registration campaign with exclusion groups

#### What the README must answer
- What's the threat model you're solving for?
- Why PIM instead of permanent role assignment?
- What trade-offs did you make between security and usability?
- How would you monitor this in production?

#### Free resources
- Microsoft Learn: Configure and manage Entra ID (SC-300 path)
- Entra ID Conditional Access documentation: learn.microsoft.com/entra/identity/conditional-access
- M365 Developer tenant (free): developer.microsoft.com/microsoft-365/dev-program

---

### Project 3 · SCIM 2.0 Provisioning Endpoint
**Status:** ⚪ Not started
**Folder:** `03-scim-server/`
**Stack:** Python 3.12, Flask, Entra ID as provisioning source

#### What it demonstrates
A working SCIM 2.0 server that Entra ID can provision users into. This is the most differentiating project — most support engineers have configured SCIM integrations hundreds of times but have never built a SCIM target.

#### What to build
- `/scim/v2/Users` endpoint: GET (list + filter), POST (create), PUT (replace), PATCH (update), DELETE
- `/scim/v2/ServiceProviderConfig` endpoint
- OAuth 2.0 client credentials auth
- Filter query parsing (`?filter=userName eq "alan"`)
- Graceful deprovisioning (soft delete, not hard delete)
- Connect Entra ID as the provisioning source and verify end-to-end

#### What the README must answer
- What does a SCIM provisioning request look like at the wire level?
- How does Entra ID discover what your SCIM server supports?
- What's the difference between PUT and PATCH in SCIM — and why does it matter?
- Lessons from building the server side vs. just configuring the client side

#### Key RFCs
- RFC 7642: SCIM definitions and concepts
- RFC 7643: SCIM core schema
- RFC 7644: SCIM protocol

#### Free resources
- Microsoft: "Develop a SCIM endpoint": learn.microsoft.com/entra/identity/app-provisioning/use-scim-to-provision-users-and-groups
- Okta SCIM guide: developer.okta.com/docs/concepts/scim

---

### Project 4 · Zero Trust Identity Architecture — Fictional Company
**Status:** ⚪ Not started
**Folder:** `04-zero-trust-design/`
**Deliverable:** PDF architecture document (not just a README)

#### What it demonstrates
Design thinking at architect level — choosing between federated vs. centralised identity, defining trust boundaries, designing JML processes. This is what IAM architects do, and publishing it shows that level of thinking.

#### Fictional client: NovaPay
*500-person fintech, Series B, 3 engineering squads, remote-first, AWS + M365, regulated (PCI-DSS). No current IDP — greenfield identity architecture.*

#### Document structure
1. Executive summary
2. Current state & threat model
3. Identity architecture decision: IDP selection (Entra ID vs Okta vs SailPoint) with rationale
4. Authentication strategy: OIDC for workforce, CIAM for customers
5. Privileged access strategy (PIM / PAM)
6. Joiner / Mover / Leaver process design
7. Non-human identity (service accounts, CI/CD pipelines)
8. Monitoring & incident response
9. Alternatives considered and rejected
10. Risk matrix

#### Free tools
- draw.io (diagrams.net) — free architecture diagrams
- Mermaid — diagrams as code, renders in GitHub
- Threat modeling: STRIDE framework (free, Microsoft)

---

### Project 5 · Auth0 CIAM Implementation
**Status:** ⚪ Not started
**Folder:** `05-auth0-ciam/`
**Stack:** Auth0 (free tier), Python or Node.js sample app

#### What it demonstrates
CIAM from the builder's side — social + enterprise SSO, custom branding, step-up auth, anomaly detection. Directly maps to Transmit Security experience and shows the CIAM design patterns that support work exposed but didn't build.

#### What to build
- Social login (Google) + enterprise SSO (Entra ID as enterprise connection)
- Custom Universal Login branding
- Auth0 Actions: step-up MFA on sensitive operations
- Anomaly detection: brute force protection, breached password detection
- Post-login Action: enrich ID token with custom claims

#### What makes this stand out
- Write a "CIAM vs workforce IAM" explainer comparing Auth0 and Transmit Security design patterns
- Document fraud prevention decisions and how they compare to DRS at Transmit Security
- Add a Loom demo video (free)

#### Free resources
- Auth0 free tier (7,500 active users): auth0.com/signup
- Auth0 learning path (free): learning.okta.com/page/development
- Auth0 docs (best CIAM implementation guides available): auth0.com/docs

---

### Project 6 · Grafana Identity Observability
**Status:** 🟡 Partially done (sanitize & publish)
**Folder:** `06-grafana-observability/`

#### What it demonstrates
Observability is a gap most IAM engineers have. Publishing the architecture and design decisions from the Grafana dashboard project at Transmit Security shows SRE-grade thinking applied to identity — a rare and valued combination.

#### What to publish (no proprietary data)
- Architecture write-up: why Prometheus + BigQuery as sources, what each monitors
- Dashboard design rationale: what signals matter for identity systems (auth failure rate, token issuance latency, provisioning lag, MFA challenge rate)
- Alerting logic: what thresholds, what on-call runbook structure
- Anonymised query patterns

#### Why this matters in interviews
*"I bring SRE-grade observability thinking to identity engineering — I've designed monitoring systems that surface auth failures, token anomalies, and provisioning lag before customers notice them."*

---

## GitHub Repository Structure

```
iam-portfolio/
├── README.md                          ← portfolio overview + your story + LinkedIn link
│
├── 01-oidc-auth-flow/
│   ├── README.md                      ← design decisions, sequence diagram, lessons
│   ├── app/                           ← working Flask app
│   └── docs/flow-diagram.png
│
├── 02-entra-ca-pim/
│   ├── README.md                      ← fictional client brief + design rationale
│   ├── policies/                      ← exported CA policy JSONs
│   └── screenshots/                   ← before/after portal states
│
├── 03-scim-server/
│   ├── README.md                      ← "building a SCIM target from scratch" write-up
│   ├── server/                        ← SCIM 2.0 endpoint implementation
│   └── tests/                         ← Postman collection for validation
│
├── 04-zero-trust-design/
│   ├── README.md
│   ├── architecture.pdf               ← the polished deliverable
│   └── diagrams/                      ← draw.io / Mermaid source files
│
├── 05-auth0-ciam/
│   ├── README.md                      ← CIAM vs workforce IAM comparison
│   ├── actions/                       ← Auth0 Actions code
│   └── docs/
│
└── 06-grafana-observability/
    ├── README.md                      ← sanitized architecture write-up
    ├── dashboards/                    ← exported Grafana JSON (no prod data)
    └── queries/                       ← Prometheus + BigQuery query patterns
```

---

## Free Resources Master List

### Environments & sandboxes
| Resource | URL | Use for |
|---|---|---|
| M365 Developer Program | developer.microsoft.com/microsoft-365/dev-program | Free Entra ID P2 tenant — Projects 1, 2, 3 |
| Okta Developer Account | developer.okta.com | Free full-featured IdP — SCIM + SSO testing |
| Auth0 Free Tier | auth0.com/signup | CIAM — Project 5 |
| Azure Free Account | azure.microsoft.com/free | App registrations, $200 credit |

### Learning
| Resource | URL | Use for |
|---|---|---|
| Microsoft Learn | learn.microsoft.com | SC-300 study path |
| Okta Learning Catalog | learning.okta.com | IAM foundations, SCIM, OIDC |
| Auth0 Docs | auth0.com/docs | Best OIDC / CIAM guides available |
| RFC 6749 | tools.ietf.org/html/rfc6749 | OAuth 2.0 source of truth |
| RFC 7636 | tools.ietf.org/html/rfc7636 | PKCE |
| RFC 7642–7644 | tools.ietf.org/html/rfc7642 | SCIM source of truth |

### Tools
| Tool | Use for |
|---|---|
| Postman (free tier) | Testing SCIM endpoints + OAuth flows |
| draw.io / diagrams.net | Architecture diagrams (Project 4) |
| Loom (free) | Demo video for Project 5 |
| dev.to / Hashnode | Publishing project write-ups |

---

## Interview Framing

### On the support-to-engineer gap
*"In Tier 3 support at this level, the line between support and implementation is intentionally blurry — I've built working replicas of customer auth flows, designed monitoring infrastructure from scratch, and advised on identity architecture. What I hadn't done was own a production deployment end-to-end. That's what this portfolio addresses directly."*

### On implementation experience
Point to the GitHub repo. Walk through the OIDC app: "Here's the PKCE verifier generation, here's the token exchange, here's why I store the token in the session this way and not localStorage."

### On observability (a differentiator)
*"I bring SRE-grade observability thinking to identity — I've designed monitoring systems that surface auth failure spikes, token anomalies, and provisioning lag before customers notice them. Most IAM engineers don't think about this until something breaks in production."*

### On CIAM specifically
*"My Transmit Security experience is in production CIAM at scale — fraud detection, risk-based authentication, adaptive challenges. Most IAM engineers have only worked on workforce identity. I've worked both sides."*

---

## Cursor Onboarding Prompt

Paste this into a new Cursor chat to resume where you left off:

> I'm Alan, a Tier 3 IAM support engineer (Transmit Security + SailPoint) building a portfolio to transition to IAM engineer. I'm working on Project 1 of 6: an OIDC / OAuth 2.0 authorization code + PKCE flow built from scratch in Python 3.12 / Flask — no SDKs handling the auth logic. IdP: Microsoft Entra ID (M365 dev tenant). Dependencies installed: flask, requests, python-dotenv. Build in 3 stages: 1) Flask skeleton + redirect to Entra ID login, 2) Callback handler — code exchange for tokens + display claims, 3) Token refresh, session management, protected routes. Explain design decisions as we go — the goal is deep understanding, not just working code. My portfolio plan is in PORTFOLIO_PLAN.md in this repo.
