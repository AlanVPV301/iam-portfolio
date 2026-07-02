# Importing FinFlow CA Policies (Path B)

These resources were built manually in the Entra portal, then imported into Terraform without recreating them. Import is **complete** in this repo — `imports.tf` was removed after a successful apply.

## Prerequisites (for a fresh tenant or re-import)

- Terraform SP auth: `ARM_TENANT_ID`, `ARM_CLIENT_ID`, `ARM_CLIENT_SECRET` in your shell
- Trusted IP: `TF_VAR_trusted_ip_cidr` (see `.env.example`)
- `terraform.tfvars` with `tenant_id` only (copy from `terraform.tfvars.example`)
- Graph app permissions: `Policy.ReadWrite.ConditionalAccess`, `Policy.Read.All` (+ admin consent)

## Running Terraform

Set the trusted IP via Terraform's env var convention, then run plan/apply from `terraform/`:

```bash
export TF_VAR_trusted_ip_cidr='203.0.113.10/32'
cd 02-entra-ca-pim/terraform
terraform plan -parallelism=1
terraform apply -parallelism=1
```

PowerShell:

```powershell
$env:TF_VAR_trusted_ip_cidr = '203.0.113.10/32'
cd 02-entra-ca-pim/terraform
terraform plan -parallelism=1
```

## Step 1 — Fetch import paths (optional / re-import)

```powershell
Connect-MgGraph -Scopes "Policy.Read.All"
cd ~/Desktop/iam-portfolio/02-entra-ca-pim/scripts
./export-terraform-import-ids.ps1
```

The script prints full import paths and refreshes `tenant_id` in `terraform.tfvars`. It does **not** write your IP to disk.

## Step 2 — Import

Use CLI import (one-time per resource):

```bash
terraform import azuread_named_location.trusted_portal /identity/conditionalAccess/namedLocations/{guid}
terraform import azuread_conditional_access_policy.mfa_high_risk_roles /identity/conditionalAccess/policies/{guid}
terraform import azuread_conditional_access_policy.compliant_device_high_risk /identity/conditionalAccess/policies/{guid}
terraform import azuread_conditional_access_policy.block_high_sign_in_risk /identity/conditionalAccess/policies/{guid}
terraform import azuread_conditional_access_policy.block_untrusted_locations /identity/conditionalAccess/policies/{guid}
terraform import azuread_conditional_access_policy.user_risk_reset /identity/conditionalAccess/policies/{guid}
```

Import paths come from `export-terraform-import-ids.ps1` or the Entra portal (full paths, not bare GUIDs).

## Step 3 — Fix drift

```bash
export TF_VAR_trusted_ip_cidr='your.real.ip/32'
terraform plan -parallelism=1
```

- **No changes** — `.tf` matches portal. Done.
- **Shows updates** — adjust `conditional_access_policies.tf` or `named_location_portal.tf` until plan is clean.
- Common drift: `state` (enabled vs report-only), auth strength vs `built_in_controls`, group order.
- **IP drift** — `TF_VAR_trusted_ip_cidr` does not match the portal. Set it to your real IP, not the placeholder.

## Path A test resources (removed)

Early Terraform create tests (`FinFlow - Terraform IAC Policy 1`, `FinFlow-Trusted-Locations-TF`) were deleted from this repo. If they still exist in state, `terraform apply` will destroy them — expected cleanup.

## Manual fallback

Import IDs must be **full Terraform paths**, not bare GUIDs from the portal:

```
/identity/conditionalAccess/namedLocations/{guid}
/identity/conditionalAccess/policies/{guid}
```

Re-run `./export-terraform-import-ids.ps1` — it prints the correct format.
