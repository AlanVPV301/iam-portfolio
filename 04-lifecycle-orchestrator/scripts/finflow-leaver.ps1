# FinFlow Ltd — Disable user, kill sessions and remove groups during leaver JML process
# Run from an authenticated Microsoft Graph PowerShell session
# Requires: Connect-MgGraph -Scopes "User.ReadWrite.All", "Group.ReadWrite.All", "Directory.ReadWrite.All"
#

param (
    [string]$Username,
    [string]$RemoveGroups

)


$ErrorActionPreference = "Stop"

# Get the project root path, then parse through the .env file keys and values
$ProjectRoot = Split-Path -Parent $PSScriptRoot
if (Test-Path "$ProjectRoot/.env") {
    Get-Content (Join-Path $ProjectRoot ".env") | ForEach-Object {
        $line = $_.Trim()
        if ($line -and !$line.StartsWith('#')) {
            $name, $value = $line.Split('=', 2)
            Set-Item -Path "Env:$name" -Value $value.Trim()        
        }
    }
}


$TenantDomain = "VPVConsulting.onmicrosoft.com"
$ClientID = $env:ENTRA_CLIENT_ID
$ClientSecret = $env:ENTRA_CLIENT_SECRET
$TenantId = $env:ENTRA_TENANT_ID


# Establish Connection via client credentials - The application permissions need User.ReadWrite.All" and "Group.ReadWrite.All
$SecureSecret = ConvertTo-SecureString $ClientSecret -AsPlainText -Force
$CREDENTIAL = New-Object System.Management.Automation.PSCredential($ClientID, $SecureSecret)

Write-Host "Connecting to Microsoft Graph..." -ForegroundColor Cyan
Connect-MgGraph -TenantId $TenantId -ClientSecretCredential $CREDENTIAL

$UPN = $Username.ToLower() + "@" + $TenantDomain


try {
    # 1. Fetch Target User and New Manager
    Write-Host "[FETCH] Fetching user and manager details..." -ForegroundColor Cyan
    $TargetUser = Get-MgUser -UserId $UPN -ErrorAction Stop

    # 2. Revoke All Sign-In Sessions Immediately
    Write-Host "Revoking all active OAuth and web sessions..." -ForegroundColor Yellow
    Revoke-MgUserSignInSession -UserId $UPN -ErrorAction SilentlyContinue

    # 3. Disable account (password reset needs User-PasswordProfile.ReadWrite.All — skip for this lab)
    Write-Host "Disabling account..." -ForegroundColor Yellow
    Update-MgUser -UserId $UPN -BodyParameter @{ AccountEnabled = $false }
 

    # 4. Process Group Offboarding (Remove Access)
    if ($RemoveGroups) {
        $RemoveGroupNames = @(
            $RemoveGroups.Split(",") |
            ForEach-Object { $_.Trim() } |
            Where-Object { $_ }
        )

        foreach ($GroupName in $RemoveGroupNames) {
            $Group = Get-MgGroup -Filter "displayName eq '$GroupName'"
            if ($Group) {
                Write-Host "[GROUPS] Removing user from group: $GroupName..." -ForegroundColor Yellow
                Remove-MgGroupMemberByRef -GroupId $Group.Id -DirectoryObjectId $TargetUser.Id -ErrorAction Stop
            }
            else {
                Write-Warning "Group '$GroupName' not found. Skipping removal."
            }
        }
    }

    # 5. Remove Assigned Microsoft 365 Licenses
    Write-Host "Retrieving assigned licenses..." -ForegroundColor Yellow
    $LicenseDetails = Get-MgUserLicenseDetail -UserId $UPN

    if ($LicenseDetails) {
        $LicensesToRemove = @()
        foreach ($Lic in $LicenseDetails) {
            $LicensesToRemove += $Lic.SkuId
        }
        
        $LicenseChanges = @{
            AddLicenses    = @()
            RemoveLicenses = $LicensesToRemove
        }
        
        Write-Host "Stripping licenses..." -ForegroundColor DarkYellow
        Set-MgUserLicense -UserId $UPN -BodyParameter $LicenseChanges
    }
    else {
        Write-Host "No direct licenses to remove." -ForegroundColor Gray
    }

    Write-Host "[SUCCESS] Mover process completed cleanly for $UPN" -ForegroundColor Green
}
catch {
    Write-Error "[FAILURE] Error processing leaver lifecycle: $_"
    Disconnect-MgGraph
    return
}

# 5. Clean up Connection Profile
Disconnect-MgGraph
Write-Host "Joiner provisioning process completed for $UPN." -ForegroundColor Green
