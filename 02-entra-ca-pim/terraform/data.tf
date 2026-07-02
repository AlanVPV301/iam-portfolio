data "azuread_group" "finance" {
  display_name = "FinFlow-Finance"
}

data "azuread_group" "engineering" {
  display_name = "FinFlow-Engineering"
}

data "azuread_group" "it_admin" {
  display_name = "FinFlow-ITAdmin"
}

data "azuread_group" "ca_exclusions" {
  display_name = "FinFlow-CA-Exclusions"
}