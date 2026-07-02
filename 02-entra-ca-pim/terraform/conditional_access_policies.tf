# FinFlow CA policies — created manually in the portal, managed here via import (Path B).
#
# Before import: copy Object IDs from Entra → Conditional Access → each policy → Properties.
# Fill import_ids in terraform.tfvars, then plan/apply with -parallelism=1.
#
# NOTE: Use .object_id on groups, not .id — CA API rejects /groups/{uuid} format.

# ── Policy 1: MFA for high-risk roles ─────────────────────────────────────────
# Portal state: On (enabled)

resource "azuread_conditional_access_policy" "mfa_high_risk_roles" {
  display_name = "FinFlow - Require MFA for High-Risk Roles"
  state        = var.ca_policy_states.mfa_high_risk_roles

  conditions {
    client_app_types = ["all"]

    applications {
      included_applications = ["All"]
    }

    users {
      included_groups = local.high_risk_group_ids
      excluded_groups = [local.ca_exclusion_group_id]
    }
  }

  grant_controls {
    operator                          = "OR"
    authentication_strength_policy_id = "/policies/authenticationStrengthPolicies/00000000-0000-0000-0000-000000000002"
  }
}

# ── Policy 2: Compliant device for high-risk roles ──────────────────────────
# Portal state: Report-only
# Requires Intune-enrolled compliant devices to enforce in practice.

resource "azuread_conditional_access_policy" "compliant_device_high_risk" {
  display_name = "FinFlow - Require Compliant Device for High-Risk Roles"
  state        = var.ca_policy_states.compliant_device

  conditions {
    client_app_types = ["all"]

    applications {
      included_applications = ["All"]
    }

    users {
      included_groups = local.high_risk_group_ids
      excluded_groups = [local.ca_exclusion_group_id]
    }
  }

  grant_controls {
    operator          = "OR"
    built_in_controls = ["compliantDevice"]
  }
}

# ── Policy 3: Sign-in risk ────────────────────────────────────────────────────
# Portal state: Report-only
# Targets all users; challenges medium + high sign-in risk (Identity Protection / P2).

resource "azuread_conditional_access_policy" "block_high_sign_in_risk" {
  display_name = "FinFlow - Block High Sign-In Risk"
  state        = var.ca_policy_states.block_high_sign_in_risk

  conditions {
    client_app_types    = ["all"]
    sign_in_risk_levels = ["high", "medium"]

    applications {
      included_applications = ["All"]
    }

    users {
      included_users  = ["All"]
      excluded_groups = [local.ca_exclusion_group_id]
    }
  }

  grant_controls {
    operator                          = "OR"
    authentication_strength_policy_id = "/policies/authenticationStrengthPolicies/00000000-0000-0000-0000-000000000002"
  }
}

# ── Policy 4: Untrusted locations ─────────────────────────────────────────────
# Portal state: Report-only
# Blocks sign-ins outside FinFlow-Trusted-Locations (portal named location).

resource "azuread_conditional_access_policy" "block_untrusted_locations" {
  display_name = "FinFlow - Block Untrusted IPs"
  state        = var.ca_policy_states.block_untrusted_locations

  conditions {
    client_app_types = ["all"]

    applications {
      included_applications = ["All"]
    }

    users {
      included_users  = ["All"]
      excluded_groups = [local.ca_exclusion_group_id]
    }

    locations {
      included_locations = ["All"]
      excluded_locations = [azuread_named_location.trusted_portal.object_id]
    }
  }

  grant_controls {
    operator          = "OR"
    built_in_controls = ["block"]
  }
}

# ── Policy 5: User risk reset ─────────────────────────────────────────────────
# Portal state: Report-only
# Requires password change + MFA when Identity Protection flags medium/high user risk.

resource "azuread_conditional_access_policy" "user_risk_reset" {
  display_name = "FinFlow-UserRisk-Reset"
  state        = var.ca_policy_states.user_risk_reset

  conditions {
    client_app_types  = ["all"]
    user_risk_levels  = ["high", "medium"]

    applications {
      included_applications = ["All"]
    }

    users {
      included_users  = ["All"]
      excluded_groups = [local.ca_exclusion_group_id]
    }
  }

  grant_controls {
    operator                          = "AND"
    authentication_strength_policy_id = "/policies/authenticationStrengthPolicies/00000000-0000-0000-0000-000000000002"
    built_in_controls                 = ["passwordChange"]
  }
}
