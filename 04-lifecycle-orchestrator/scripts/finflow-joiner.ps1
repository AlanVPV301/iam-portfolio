# FinFlow Ltd — Test user and group creation
# Run from an authenticated Microsoft Graph PowerShell session
# Requires: Connect-MgGraph -Scopes "User.ReadWrite.All", "Group.ReadWrite.All", "Directory.ReadWrite.All"
#

param (
    [string]$Username,
    [string]$FirstName,
    [string]$LastName,
    [string]$Department,
    [string]$Email,
    [string]$JobTitle,
    [string]$TargetGroups
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

$GroupNames = @(
    $TargetGroups.Split(",") |
    ForEach-Object { $_.Trim() } |
    Where-Object { $_ }
)

$TenantDomain = "VPVConsulting.onmicrosoft.com"
$TempPassword = $env:FINFLOW_USER_PASSWORD
$ClientID = $env:ENTRA_CLIENT_ID
$ClientSecret = $env:ENTRA_CLIENT_SECRET
$TenantId = $env:ENTRA_TENANT_ID


if (-not $TempPassword) {
    Write-Host "FINFLOW_USER_PASSWORD is not set. Run:" -ForegroundColor Yellow
    Write-Host "  export FINFLOW_USER_PASSWORD='your-temp-password-here'" -ForegroundColor Cyan
    exit 1
}

$PasswordProfile = @{
    Password                      = $TempPassword
    ForceChangePasswordNextSignIn = $false
}

#$TargetGroups = @("FinFlow-Engineering") 


# Establish Connection via client credentials - The application permissions need User.ReadWrite.All" and "Group.ReadWrite.All
$SecureSecret = ConvertTo-SecureString $ClientSecret -AsPlainText -Force
$CREDENTIAL = New-Object System.Management.Automation.PSCredential($ClientID, $SecureSecret)

Write-Host "Connecting to Microsoft Graph..." -ForegroundColor Cyan
Connect-MgGraph -TenantId $TenantId -ClientSecretCredential $CREDENTIAL

# 3. Create User Account
$UserParams = @{
    AccountEnabled    = $true
    DisplayName       = "$FirstName $LastName"
    GivenName         = $FirstName
    Surname           = $LastName
    MailNickname      = $Username.ToLower()
    UserPrincipalName = $Username.ToLower() + "@" + $TenantDomain
    Department        = $Department
    JobTitle          = $JobTitle
    PasswordProfile   = $PasswordProfile
    Mail              = $Email
}


try {
    Write-Host "Provisioning user account for $DisplayName..." -ForegroundColor Cyan
    $NewUser = New-MgUser @UserParams
    Write-Host "Success: User created with ID: $($NewUser.Id)" -ForegroundColor Green
}
catch {
    Write-Error "Failed to create user: $_"
    Disconnect-MgGraph
    return
}

foreach ($Group in $GroupNames) {
    $Group = Get-MgGroup -Filter "displayName eq '$($Group)'"
    if ($Group) {
        New-MgGroupMember -GroupId $Group.Id -DirectoryObjectId $NewUser.Id
        Write-Host "  Added to group: $($Group)"
    }
    else {
        Write-Host "  WARNING: Group '$($Group)' not found — skipping membership"
    }
}

# 5. Clean up Connection Profile
Disconnect-MgGraph
Write-Host "Joiner provisioning process completed for $DisplayName." -ForegroundColor Green
