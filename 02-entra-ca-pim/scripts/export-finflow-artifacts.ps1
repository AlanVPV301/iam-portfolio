# FinFlow Ltd — Export CA policies and named locations to JSON
#
# Writes one file per policy/location under ../policies/ (portfolio evidence + backup).
#
# Prerequisites:
#   Connect-MgGraph -Scopes "Policy.Read.All"
#
# Usage:
#   ./export-finflow-artifacts.ps1
#   ./export-finflow-artifacts.ps1 -OutputDir ../policies

param(
    [string]$OutputDir = (Join-Path $PSScriptRoot ".." "policies")
)

$ErrorActionPreference = "Stop"

# Export anything whose display name starts with this prefix
$NamePrefix = "FinFlow"

# Verifies an active Connect-MgGraph session exists before calling Graph.
function Test-MgGraphConnection {
    $context = Get-MgContext -ErrorAction SilentlyContinue
    if (-not $context) {
        Write-Host "Not connected to Graph. Run:" -ForegroundColor Yellow
        Write-Host '  Connect-MgGraph -Scopes "Policy.Read.All"' -ForegroundColor Cyan
        exit 1
    }
    Write-Host "Connected as: $($context.Account)" -ForegroundColor DarkGray
}

# Turns a display name into a safe filename (removes invalid path characters).
function ConvertTo-SafeFileName {
    param([string]$Name)
    return ($Name -replace '[\\/:*?"<>|]', '-').Trim()
}

# Exports all FinFlow CA policies as individual JSON files + one combined file.
function Export-ConditionalAccessPolicies {
    param([string]$Directory)

    $policiesDir = Join-Path $Directory "conditional-access"
    New-Item -ItemType Directory -Force -Path $policiesDir | Out-Null

    $policies = Get-MgIdentityConditionalAccessPolicy -All `
        | Where-Object { $_.DisplayName -like "$NamePrefix*" } `
        | Sort-Object DisplayName

    if (-not $policies) {
        Write-Warning "No CA policies found matching '$NamePrefix*'"
        return
    }

    foreach ($policy in $policies) {
        $fileName = "$(ConvertTo-SafeFileName -Name $policy.DisplayName).json"
        $filePath = Join-Path $policiesDir $fileName

        $policy | ConvertTo-Json -Depth 20 | Set-Content -Path $filePath -Encoding utf8NoBOM
        Write-Host "  Policy: $($policy.DisplayName) -> $fileName" -ForegroundColor Green
    }

    $combinedPath = Join-Path $policiesDir "_all-finflow-policies.json"
    $policies | ConvertTo-Json -Depth 20 | Set-Content -Path $combinedPath -Encoding utf8NoBOM
    Write-Host "  Combined: _all-finflow-policies.json ($($policies.Count) policies)" -ForegroundColor Green
}

# Exports all FinFlow named locations as individual JSON files + one combined file.
function Export-NamedLocations {
    param([string]$Directory)

    $locationsDir = Join-Path $Directory "named-locations"
    New-Item -ItemType Directory -Force -Path $locationsDir | Out-Null

    $locations = Get-MgIdentityConditionalAccessNamedLocation -All `
        | Where-Object { $_.DisplayName -like "$NamePrefix*" } `
        | Sort-Object DisplayName

    if (-not $locations) {
        Write-Warning "No named locations found matching '$NamePrefix*'"
        return
    }

    foreach ($location in $locations) {
        $fileName = "$(ConvertTo-SafeFileName -Name $location.DisplayName).json"
        $filePath = Join-Path $locationsDir $fileName

        $location | ConvertTo-Json -Depth 20 | Set-Content -Path $filePath -Encoding utf8NoBOM
        Write-Host "  Location: $($location.DisplayName) -> $fileName" -ForegroundColor Green
    }

    $combinedPath = Join-Path $locationsDir "_all-finflow-locations.json"
    $locations | ConvertTo-Json -Depth 20 | Set-Content -Path $combinedPath -Encoding utf8NoBOM
    Write-Host "  Combined: _all-finflow-locations.json ($($locations.Count) locations)" -ForegroundColor Green
}

# Writes a short manifest with export timestamp and file counts.
function Write-ExportManifest {
    param([string]$Directory)

    $manifest = [ordered]@{
        exported_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        prefix      = $NamePrefix
        paths       = @{
            conditional_access = "conditional-access/"
            named_locations    = "named-locations/"
        }
        note        = "Portal JSON exports via Microsoft Graph. Screenshots (PIM, Secure Score) are manual."
    }

    $manifestPath = Join-Path $Directory "manifest.json"
    $manifest | ConvertTo-Json -Depth 5 | Set-Content -Path $manifestPath -Encoding utf8NoBOM
    Write-Host "  Manifest: manifest.json" -ForegroundColor Green
}

# ── Main ──────────────────────────────────────────────────────────────────────

Test-MgGraphConnection

Write-Host "`nExporting to: $OutputDir" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

Write-Host "`nConditional Access policies:" -ForegroundColor Cyan
Export-ConditionalAccessPolicies -Directory $OutputDir

Write-Host "`nNamed locations:" -ForegroundColor Cyan
Export-NamedLocations -Directory $OutputDir

Write-Host "`nManifest:" -ForegroundColor Cyan
Write-ExportManifest -Directory $OutputDir

Write-Host "`nDone." -ForegroundColor Yellow
Write-Host "Screenshots still needed manually: PIM settings, Secure Score, MFA campaign, What If results."
