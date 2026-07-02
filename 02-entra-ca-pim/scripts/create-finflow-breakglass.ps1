# FinFlow Ltd — Break glass account creation and Global Administrator role configuration
# Run from an authenticated Microsoft Graph PowerShell session
# Requires: Connect-MgGraph -Scopes "User.ReadWrite.All", "RoleManagement.ReadWrite.Directory"
#
# Set password before running (never commit this value):
#   export FINFLOW_BREAKGLASS_PASSWORD='your-breakglass-password-here'

$ErrorActionPreference = "Stop"

$BreakGlassPassword = $env:FINFLOW_BREAKGLASS_PASSWORD

if (-not $BreakGlassPassword) {
    Write-Host "FINFLOW_BREAKGLASS_PASSWORD is not set. Run:" -ForegroundColor Yellow
    Write-Host "  export FINFLOW_BREAKGLASS_PASSWORD='your-breakglass-password-here'" -ForegroundColor Cyan
    exit 1
}

$PasswordProfile = @{
    Password                      = $BreakGlassPassword
    ForceChangePasswordNextSignIn = $false
}

$BG = New-MgUser `
    -DisplayName "Break Glass Admin" `
    -UserPrincipalName "breakglass@VPVConsulting.onmicrosoft.com" `
    -MailNickname "breakglass" `
    -AccountEnabled `
    -PasswordProfile $PasswordProfile

Write-Host "Break glass account created: $($BG.Id)"

# Get the Global Administrator role definition
$Role = Get-MgDirectoryRole -Filter "displayName eq 'Global Administrator'"

# If the role hasn't been activated in this tenant yet, activate it first
if (-not $Role) {
    $RoleTemplate = Get-MgDirectoryRoleTemplate -Filter "displayName eq 'Global Administrator'"
    $Role = New-MgDirectoryRole -RoleTemplateId $RoleTemplate.Id

    Write-Host "Role activated: $($Role.Id)"
}

# Assign using the newer cmdlet
$Params = @{
    "@odata.id" = "https://graph.microsoft.com/v1.0/directoryObjects/$($BG.Id)"
}

New-MgDirectoryRoleMemberByRef -DirectoryRoleId $Role.Id -BodyParameter $Params

Write-Host "Global Administrator assigned to $($BG.UserPrincipalName)"
