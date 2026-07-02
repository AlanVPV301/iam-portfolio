# FinFlow Ltd — Test user and group creation
# Run from an authenticated Microsoft Graph PowerShell session
# Requires: Connect-MgGraph -Scopes "User.ReadWrite.All", "Group.ReadWrite.All", "Directory.ReadWrite.All"
#
# Set password before running (never commit this value):
#   export FINFLOW_USER_PASSWORD='your-temp-password-here'

$ErrorActionPreference = "Stop"

$TenantDomain = "VPVConsulting.onmicrosoft.com"
$TempPassword = $env:FINFLOW_USER_PASSWORD

if (-not $TempPassword) {
    Write-Host "FINFLOW_USER_PASSWORD is not set. Run:" -ForegroundColor Yellow
    Write-Host "  export FINFLOW_USER_PASSWORD='your-temp-password-here'" -ForegroundColor Cyan
    exit 1
}

$Users = @(
    @{ DisplayName = "Alice Finance";    Username = "alice.finance";    Group = "FinFlow-Finance" },
    @{ DisplayName = "Bob Engineering";  Username = "bob.engineering";  Group = "FinFlow-Engineering" },
    @{ DisplayName = "Carol ITAdmin";    Username = "carol.itadmin";    Group = "FinFlow-ITAdmin" },
    @{ DisplayName = "Dave Standard";    Username = "dave.standard";    Group = $null }
)

$PasswordProfile = @{
    Password                      = $TempPassword
    ForceChangePasswordNextSignIn = $false
}

foreach ($u in $Users) {
    $UPN = "$($u.Username)@$TenantDomain"

    Write-Host "Creating user: $UPN"

    $NewUser = New-MgUser `
        -DisplayName      $u.DisplayName `
        -UserPrincipalName $UPN `
        -MailNickname     $u.Username `
        -AccountEnabled   `
        -PasswordProfile  $PasswordProfile

    Write-Host "  Created: $($NewUser.Id)"

    if ($u.Group) {
        $Group = Get-MgGroup -Filter "displayName eq '$($u.Group)'"
        if ($Group) {
            New-MgGroupMember -GroupId $Group.Id -DirectoryObjectId $NewUser.Id
            Write-Host "  Added to group: $($u.Group)"
        } else {
            Write-Host "  WARNING: Group '$($u.Group)' not found — skipping membership"
        }
    }
}

Write-Host "`nDone. All users created."
