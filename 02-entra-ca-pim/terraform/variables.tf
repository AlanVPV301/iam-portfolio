# ── Tenant ────────────────────────────────────────────────────────────────────

variable "tenant_id" {
  type        = string
  description = "Entra ID tenant ID (Directory ID)"
}

variable "trusted_ip_cidr" {
  type        = string
  description = "Trusted location IP in CIDR notation. Set via env before plan/apply: export TF_VAR_trusted_ip_cidr='203.0.113.10/32'"
}

# ── CA policy enforcement states ────────────────────────────────────────────
# enabled                          = enforcing
# enabledForReportingButNotEnforced = report-only
# disabled                         = off

variable "ca_policy_states" {
  type = object({
    mfa_high_risk_roles       = string
    compliant_device          = string
    block_high_sign_in_risk   = string
    block_untrusted_locations = string
    user_risk_reset           = string
  })
  description = "Enforcement state for each FinFlow CA policy — match the portal"
  default = {
    mfa_high_risk_roles       = "enabled"
    compliant_device          = "enabledForReportingButNotEnforced"
    block_high_sign_in_risk   = "enabledForReportingButNotEnforced"
    block_untrusted_locations = "enabledForReportingButNotEnforced"
    user_risk_reset           = "enabledForReportingButNotEnforced"
  }

  validation {
    condition = alltrue([
      for state in values(var.ca_policy_states) :
      contains(["enabled", "disabled", "enabledForReportingButNotEnforced"], state)
    ])
    error_message = "Policy state must be enabled, disabled, or enabledForReportingButNotEnforced."
  }
}

# ── Import Object IDs (Path B — one-time setup) ───────────────────────────────
# Populated by ../scripts/export-terraform-import-ids.ps1 during initial import.
# Not referenced by .tf after import completes.
