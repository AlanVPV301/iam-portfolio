# FinFlow Ltd — Test user and group creation
# Run from an authenticated Microsoft Graph PowerShell session
# Requires: Connect-MgGraph -Scopes "User.ReadWrite.All", "Group.ReadWrite.All", "Directory.ReadWrite.All"
#



$ErrorActionPreference = "Stop"

# Get the project root path, then parse through the .env file keys and values
$ProjectRoot = Split-Path -Parent $PSScriptRoot
if (Test-Path "$ProjectRoot/.env") {
    Get-Content .env | ForEach-Object {
        $line = $_.Trim()
        if ($line -and !$line.StartsWith('#')) {
            $name, $value = $line.Split('=', 2)
            Set-Item -Path "Env:$name" -Value $value.Trim()        
        }
    }
}



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

# New Hire Identity Details
$FirstName = "John"
$LastName = "Doe"
$DisplayName = "$FirstName $LastName"
$UPN = "john.doe@$TenantDomain"
$JobTitle = "Cloud Engineer"
$Department = "Information Technology"
$UsageLocation = "US"

$PasswordProfile = @{
    Password                      = $TempPassword
    ForceChangePasswordNextSignIn = $false
}

$TargetGroups = @("FinFlow-Engineering") # Replace with actual Object IDs


# Establish Connection via client credentials - The application permissions need User.ReadWrite.All" and "Group.ReadWrite.All
$SecureSecret = ConvertTo-SecureString $ClientSecret -AsPlainText -Force
$CREDENTIAL = New-Object System.Management.Automation.PSCredential($ClientID, $SecureSecret)

Write-Host "Connecting to Microsoft Graph..." -ForegroundColor Cyan
Connect-MgGraph -TenantId $TenantId -ClientSecretCredential $CREDENTIAL

# 3. Create User Account
$UserParams = @{
    AccountEnabled    = $true
    DisplayName       = $DisplayName
    GivenName         = $FirstName
    Surname           = $LastName
    UserPrincipalName = $UPN
    MailNickname      = $FirstName.ToLower() + "." + $LastName.ToLower()
    JobTitle          = $JobTitle
    Department        = $Department
    UsageLocation     = $UsageLocation
    PasswordProfile   = $PasswordProfile
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

foreach ($Group in $TargetGroups) {
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
