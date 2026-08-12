# FinFlow Ltd — Update user attributes and groups during mover JML process
# Run from an authenticated Microsoft Graph PowerShell session
# Requires: Connect-MgGraph -Scopes "User.ReadWrite.All", "Group.ReadWrite.All", "Directory.ReadWrite.All"
#

param (
    [string]$Username,
    [string]$Department,
    [string]$Email,
    [string]$JobTitle,
    [string]$AddGroups,
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

    $UpdateParams = @{}

    if ($Department) {
        $UpdateParams.Add('Department', $Department)
    
    }
    if ($Email) {
        $UpdateParams.Add('Mail', $Email)
    
    }

    if ($JobTitle) {
        $UpdateParams.Add('JobTitle', $JobTitle)
    
    }

    # 2. Update User Profile Properties
    Write-Host "[UPDATE] Updating user properties..." -ForegroundColor Green
    Update-MgUser -UserId $TargetUser.Id -BodyParameter $UpdateParams
 

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

    # 5. Process Group Onboarding (Grant Access)
    if ($AddGroups) {
        $AddGroupNames = @(
            $AddGroups.Split(",") |
            ForEach-Object { $_.Trim() } |
            Where-Object { $_ }
        )
        foreach ($Group in $AddGroupNames) {
            $Group = Get-MgGroup -Filter "displayName eq '$($Group)'"
            if ($Group) {
                New-MgGroupMember -GroupId $Group.Id -DirectoryObjectId $TargetUser.Id
                Write-Host "  Added to group: $($Group)"
            }
            else {
                Write-Host "  WARNING: Group '$($Group)' not found — skipping membership"
            }
        }
    }
    Write-Host "[SUCCESS] Mover process completed cleanly for $UPN" -ForegroundColor Green
}
catch {
    Write-Error "[FAILURE] Error processing mover lifecycle: $_"
    Disconnect-MgGraph
    return
}

# 5. Clean up Connection Profile
Disconnect-MgGraph
Write-Host "Joiner provisioning process completed for $UPN." -ForegroundColor Green
