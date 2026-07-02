# FinFlow Ltd — Fetch Entra CA policy / named location Object IDs for Terraform import
#
# Queries Graph by display name and writes IDs into terraform/terraform.tfvars.
#
# Prerequisites:
#   Connect-MgGraph -Scopes "Policy.Read.All"
#
# Usage:
#   ./export-terraform-import-ids.ps1

param(
    [string]$TerraformDir = (Join-Path $PSScriptRoot ".." "terraform")
)

$ErrorActionPreference = "Stop"

# Must match display_name values in conditional_access_policies.tf / named_location_portal.tf
$NamedLocationDisplayName = "FinFlow-Trusted-IP-Locations"

$PolicyDisplayNames = [ordered]@{
    mfa_high_risk_roles       = "FinFlow - Require MFA for High-Risk Roles"
    compliant_device          = "FinFlow - Require Compliant Device for High-Risk Roles"
    block_high_sign_in_risk   = "FinFlow - Block High Sign-In Risk"
    block_untrusted_locations = "FinFlow - Block Untrusted IPs"
    user_risk_reset           = "FinFlow-UserRisk-Reset"
}

# Verifies an active Connect-MgGraph session exists before we call any Graph cmdlets.
function Test-MgGraphConnection {
    $context = Get-MgContext -ErrorAction SilentlyContinue
    if (-not $context) {
        Write-Host "Not connected to Graph. Run:" -ForegroundColor Yellow
        Write-Host '  Connect-MgGraph -Scopes "Policy.Read.All"' -ForegroundColor Cyan
        exit 1
    }
    Write-Host "Connected as: $($context.Account)" -ForegroundColor DarkGray
}

# Lists all named locations and returns the Object ID for the given display name.
function Get-ConditionalAccessNamedLocationByName {
    param([string]$DisplayName)

    $location = Get-MgIdentityConditionalAccessNamedLocation -All `
        | Where-Object { $_.DisplayName -eq $DisplayName } `
        | Select-Object -First 1

    if (-not $location) {
        throw "Named location not found: '$DisplayName'"
    }

    return $location.Id
}

# Wraps a bare Graph GUID in the path format Terraform import requires.
function ConvertTo-TerraformNamedLocationImportId {
    param([string]$ObjectId)
    return "/identity/conditionalAccess/namedLocations/$ObjectId"
}

# Lists all CA policies and returns the Object ID for the given display name.
function Get-ConditionalAccessPolicyByName {
    param([string]$DisplayName)

    $policy = Get-MgIdentityConditionalAccessPolicy -All `
        | Where-Object { $_.DisplayName -eq $DisplayName } `
        | Select-Object -First 1

    if (-not $policy) {
        throw "CA policy not found: '$DisplayName'"
    }

    return $policy.Id
}

# Wraps a bare Graph GUID in the path format Terraform import requires.
function ConvertTo-TerraformConditionalAccessPolicyImportId {
    param([string]$ObjectId)
    return "/identity/conditionalAccess/policies/$ObjectId"
}

# Reads tenant_id from tfvars, env (FINFLOW_TENANT_ID / TF_VAR_tenant_id), or Graph context.
function Read-TfvarsBaseConfig {
    param([string]$TfvarsPath)

    $tenantId = $null

    if (Test-Path $TfvarsPath) {
        $content = Get-Content $TfvarsPath -Raw
        if ($content -match 'tenant_id\s*=\s*"([^"]+)"') {
            $tenantId = $Matches[1]
        }
    }

    if (-not $tenantId -and $env:FINFLOW_TENANT_ID) {
        $tenantId = $env:FINFLOW_TENANT_ID
    }
    if (-not $tenantId -and $env:TF_VAR_tenant_id) {
        $tenantId = $env:TF_VAR_tenant_id
    }
    if (-not $tenantId) {
        $context = Get-MgContext -ErrorAction SilentlyContinue
        if ($context.TenantId) {
            $tenantId = $context.TenantId
        }
    }

    return @{
        TenantId = $tenantId
    }
}

# Writes terraform.tfvars with tenant_id only (IP via TF_VAR_trusted_ip_cidr env var).
function Write-TerraformTfvars {
    param(
        [string]$TfvarsPath,
        [string]$TenantId
    )

    if (-not $TenantId) {
        throw "tenant_id not found. Set in $TfvarsPath, FINFLOW_TENANT_ID, or connect Graph with Connect-MgGraph"
    }

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $lines = @(
        "tenant_id = `"$TenantId`""
        ""
        "# trusted_ip_cidr — set via TF_VAR_trusted_ip_cidr before terraform plan/apply"
        "# Updated by export-terraform-import-ids.ps1 on $timestamp"
        ""
    )

    Set-Content -Path $TfvarsPath -Value ($lines -join "`n") -Encoding utf8NoBOM
}

# ── Main ──────────────────────────────────────────────────────────────────────

Test-MgGraphConnection

$tfvarsPath = Join-Path $TerraformDir "terraform.tfvars"
$baseConfig = Read-TfvarsBaseConfig -TfvarsPath $tfvarsPath

Write-Host "`nFetching named location: $NamedLocationDisplayName" -ForegroundColor Cyan
$locationId = Get-ConditionalAccessNamedLocationByName -DisplayName $NamedLocationDisplayName `
    | ForEach-Object { ConvertTo-TerraformNamedLocationImportId -ObjectId $_ }
Write-Host "  ID: $locationId" -ForegroundColor Green

$policyIds = [ordered]@{}
foreach ($key in $PolicyDisplayNames.Keys) {
    $displayName = $PolicyDisplayNames[$key]
    Write-Host "Fetching policy: $displayName" -ForegroundColor Cyan
    $rawId = Get-ConditionalAccessPolicyByName -DisplayName $displayName
    $policyIds[$key] = ConvertTo-TerraformConditionalAccessPolicyImportId -ObjectId $rawId
    Write-Host "  ID: $($policyIds[$key])" -ForegroundColor Green
}

Write-Host "`nWriting $tfvarsPath" -ForegroundColor Cyan
Write-TerraformTfvars -TfvarsPath $tfvarsPath -TenantId $baseConfig.TenantId

Write-Host "`nImport paths (for terraform import — one-time):" -ForegroundColor Yellow
Write-Host "  named location: $locationId"
foreach ($key in $PolicyIds.Keys) {
    Write-Host "  $key`: $($policyIds[$key])"
}

Write-Host "`nDone. Next steps:" -ForegroundColor Yellow
Write-Host "  export TF_VAR_trusted_ip_cidr='your.public.ip/32'"
Write-Host "  cd $TerraformDir"
Write-Host "  terraform plan -parallelism=1"
