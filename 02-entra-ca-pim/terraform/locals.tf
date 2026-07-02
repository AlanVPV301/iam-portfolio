# Shared targeting for FinFlow high-risk role policies (Finance, Engineering, IT Admin).
locals {
  high_risk_group_ids = [
    data.azuread_group.finance.object_id,
    data.azuread_group.engineering.object_id,
    data.azuread_group.it_admin.object_id,
  ]

  ca_exclusion_group_id = data.azuread_group.ca_exclusions.object_id
}
