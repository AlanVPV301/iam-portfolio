# Manual trusted location created in the Entra portal (Path B).
# Managed in Terraform after import — see IMPORT.md.

resource "azuread_named_location" "trusted_portal" {
  display_name = "FinFlow-Trusted-IP-Locations"

  ip {
    ip_ranges = [var.trusted_ip_cidr]
    trusted   = true
  }
}
