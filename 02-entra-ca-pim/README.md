# Project 2 — Entra ID Conditional Access & PIM

Design and initial implementation of a Conditional Access policy suite and Privileged Identity Management configuration for a fictional mid-size fintech moving toward zero trust. Includes PowerShell automation for identity provisioning and policy export, plus Terraform to codify CA policies and named locations.

**Stack:** Microsoft Entra ID (M365 dev tenant), Microsoft Graph PowerShell, Terraform (`azuread` provider)

---

## Client brief (Fictional, AI-Created)

**FinFlow Ltd** — 400-person fintech, hybrid workforce, Microsoft 365 E3, regulated environment (PCI-DSS adjacent). Moving from ad-hoc admin access and inconsistent MFA enforcement to a zero-trust identity baseline.

High-risk populations: **Finance**, **Engineering**, **IT Admin**.

THe intention with this project was to treat the brief as a real client engagement: threat model first, implement in the portal, validate with What If, then codify in IaC.

---

## What this project demonstrates

- Designing a layered CA policy suite (identity, device, risk, location)
- Just-in-time privileged access with PIM — approval, justification, time-bound activation
- Break-glass emergency access design
- Automating identity operations with Microsoft Graph PowerShell
- Importing manually-built Entra config into Terraform without recreating it

---

## Architecture overview

```
Users / Groups (FinFlow-*)
        │
        ▼
Conditional Access ──► MFA (high-risk roles)
                     ──► Compliant device (high-risk roles)
                     ──► Sign-in risk (all users)
                     ──► Block untrusted locations (all users)
        │
        ▼
PIM (Entra roles) ──► Eligible assignments + activation workflow
        │
        ▼
Break-glass account ──► Standing Global Admin, excluded from all CA
```

**Key groups**


| Group                   | Purpose                                                    |
| ----------------------- | ---------------------------------------------------------- |
| `FinFlow-Finance`       | High-risk — Finance department                             |
| `FinFlow-Engineering`   | High-risk — Engineering department                         |
| `FinFlow-ITAdmin`       | High-risk — IT Admin department                            |
| `FinFlow-CA-Exclusions` | Break-glass + accounts excluded from CA policies           |
| `FinFlow-PIM-Approvers` | Approves PIM activation requests (separate from requestor) |


**Test users** (created via `scripts/create-finflow-users.ps1`): Alice Finance, Bob Engineering, Carol ITAdmin, Dave Standard (no high-risk group).

---

## Design decisions

### Why Conditional Access?

CA is the enforcement layer for zero trust in Entra — it evaluates signals (user, device, location, risk) at sign-in and applies controls before access is granted. Policy-based beats manual per-app configuration as the org scales.

### Why PIM instead of permanent role assignment?

Standing privileged access is a permanent attack surface. If an admin account is compromised, the attacker inherits Global Admin immediately. PIM converts permanent assignment to **eligible** assignment: the user must request activation, provide justification, get approval, and the elevation auto-expires. Every activation is auditable.

In this implementation, self-approval is blocked at the platform level — the requestor and approver must be different identities.

### Break-glass account

`breakglass@` holds **permanent** Global Administrator and is a member of `FinFlow-CA-Exclusions`. If a CA policy misconfiguration locks out all admins, this account can still sign in. It is not enrolled in PIM — emergency access must not depend on activation workflows or MFA chains that could fail during an outage.

### Report-only before enforce

Policies were created in **report-only** mode first and validated with **What If** before switching to enforce. This avoids locking users out while targeting is verified — standard practice in a real client rollout.

Only the high-risk MFA policy runs **On** initially; device, sign-in risk, and location policies stay report-only until Intune enrollment and tuning are complete.

### Security vs usability trade-offs


| Decision                                                        | Security                                                        | Usability                                               |
| --------------------------------------------------------------- | --------------------------------------------------------------- | ------------------------------------------------------- |
| MFA enforced for high-risk roles only (not all users initially) | Stronger on sensitive populations                               | Standard users unaffected during rollout                |
| Compliant device in report-only                                 | Documented requirement without blocking everyone without Intune | Dev tenant has no enrolled devices or Intune configured |
| PIM approval required                                           | Second pair of eyes on elevation                                | Extra step for admins                                   |
| Break-glass excluded from CA                                    | Guaranteed recovery path                                        | Must be tightly controlled and audited                  |


---

## What was implemented

### Identity structure

- **Groups:** created manually in portal (`FinFlow-Finance`, `FinFlow-Engineering`, `FinFlow-ITAdmin`, `FinFlow-CA-Exclusions`, `FinFlow-PIM-Approvers`)
- **Users:** created via PowerShell (`scripts/create-finflow-users.ps1`)
- **Break-glass:** created via PowerShell (`scripts/create-finflow-breakglass.ps1`) with standing Global Admin

### Conditional Access policies


| Policy                                                 | Target                                                   | Grant                                              | State                                                                           |
| ------------------------------------------------------ | -------------------------------------------------------- | -------------------------------------------------- | ------------------------------------------------------------------------------- |
| FinFlow - Require MFA for High-Risk Roles              | Finance, Engineering, IT Admin groups                    | MFA (authentication strength)                      | **On**                                                                          |
| FinFlow - Require Compliant Device for High-Risk Roles | Same high-risk groups                                    | Require compliant device                           | Report-only                                                                     |
| FinFlow - Block High Sign-In Risk                      | All users (excl. CA exclusions)                          | MFA on medium/high sign-in risk                    | Report-only                                                                     |
| FinFlow - Block Untrusted IPs                          | All users (excl. CA exclusions + trusted named location) | Block                                              | Report-only                                                                     |
| FinFlow-UserRisk-Reset                                 | All users (excl. CA exclusions)                          | Password change + MFA on medium/high **user** risk | Report-only                                                                     |


**Named location:** `FinFlow-Trusted-IP-Locations` — trusted IP range for office/home testing. In a production setting, this would include the office locations as well as trusted VPN/Secure networks. 

Exported JSON: `policies/conditional-access/` and `policies/named-locations/` (via `scripts/export-finflow-artifacts.ps1`).

### Privileged Identity Management


| Role                 | Assignment                                | Activation settings                                                                     |
| -------------------- | ----------------------------------------- | --------------------------------------------------------------------------------------- |
| Global Administrator | Eligible (admin account)                  | 8h max, MFA on activation, justification required, approval via `FinFlow-PIM-Approvers` |
| Global Administrator | **Active / permanent** (break-glass only) | N/A — emergency access                                                                  |


Activation flow tested: request → approve as break-glass → time-limited active assignment.

---

## Infrastructure as Code

### What is codified in Terraform

- 5 FinFlow CA policies (`terraform/conditional_access_policies.tf`) — MFA, compliant device, sign-in risk, untrusted locations, user risk reset
- Portal named location `FinFlow-Trusted-IP-Locations` (`terraform/named_location_portal.tf`)
- Group targeting via data sources (`terraform/data.tf`)

See `terraform/IMPORT.md` for how portal resources were imported.

**Secrets / IP:** Set `TF_VAR_trusted_ip_cidr` before plan/apply (never commit your real IP). See `.env.example`.

---

## Repository structure

```
02-entra-ca-pim/
├── scripts/
│   ├── create-finflow-users.ps1          # Test users + group membership
│   ├── create-finflow-breakglass.ps1     # Break-glass account + GA role
│   ├── export-terraform-import-ids.ps1    # Print import paths; refresh tenant_id in tfvars
│   └── export-finflow-artifacts.ps1       # Export CA policies/locations → JSON
├── terraform/                            # CA + named location IaC
├── policies/
│   ├── conditional-access/               # Exported policy JSON (Graph)
│   └── named-locations/
└── README.md
```

---

## Monitoring in production


| Signal                    | Source                           | Use                                                   |
| ------------------------- | -------------------------------- | ----------------------------------------------------- |
| CA policy hits / failures | Entra sign-in logs + CA insights | Tune policies, detect misconfiguration                |
| PIM activations           | PIM audit logs + Entra audit     | Who elevated, when, justification                     |
| Risk detections           | Identity Protection              | Feed sign-in/user risk policies                       |
| Secure Score trend        | Entra Secure Score               | Track posture improvement over time                   |
| Break-glass usage         | Sign-in logs for break-glass UPN | Alert on any break-glass sign-in — always investigate |


Break-glass sign-in should trigger an immediate alert in production.