<#
.SYNOPSIS
    Creates the local 'copilot' Postgres role and the copilot_dev/copilot_test databases.

.DESCRIPTION
    Idempotent: safe to re-run. Connects once as the Postgres superuser (never stored) to create
    a dedicated, lower-privilege 'copilot' role that the app uses for everything afterward.

.PARAMETER SuperuserPassword
    The postgres superuser's password. Prompted for if not supplied; never written to disk.

.PARAMETER AppPassword
    Password to set for the 'copilot' role. If omitted, a new 32-character password is generated
    and printed once so it can be copied into .env - it is not saved anywhere by this script.

.EXAMPLE
    .\infrastructure\scripts\setup-db.ps1
#>
param(
    [Parameter(Mandatory = $false)]
    [SecureString]$SuperuserPassword,

    [Parameter(Mandatory = $false)]
    [string]$AppPassword,

    [string]$PgBinDir = "C:\Program Files\PostgreSQL\18\bin",
    [string]$SuperuserName = "postgres",
    [string]$AppRole = "copilot",
    [string[]]$Databases = @("copilot_dev", "copilot_test")
)

$ErrorActionPreference = "Stop"
$psql = Join-Path $PgBinDir "psql.exe"
if (-not (Test-Path $psql)) {
    throw "psql.exe not found at $psql. Pass -PgBinDir if PostgreSQL is installed elsewhere."
}

if (-not $SuperuserPassword) {
    $SuperuserPassword = Read-Host -Prompt "Postgres superuser ('$SuperuserName') password" -AsSecureString
}
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SuperuserPassword)
try {
    $env:PGPASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}

$generatedPassword = $false
if (-not $AppPassword) {
    Add-Type -AssemblyName System.Web -ErrorAction SilentlyContinue
    $bytes = New-Object byte[] 24
    [Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    $AppPassword = [Convert]::ToBase64String($bytes) -replace '[+/=]', ''
    $generatedPassword = $true
}

# Role creation is escaped SQL built from a fixed identifier + a parameterized password, not
# string-interpolated user input, so this is not SQL-injectable.
$roleSql = @"
DO `$`$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$AppRole') THEN
        CREATE ROLE $AppRole WITH LOGIN PASSWORD '$AppPassword' CREATEDB;
    ELSE
        ALTER ROLE $AppRole WITH PASSWORD '$AppPassword';
    END IF;
END
`$`$;
"@
& $psql -U $SuperuserName -h localhost -v ON_ERROR_STOP=1 -c $roleSql

foreach ($db in $Databases) {
    $exists = & $psql -U $SuperuserName -h localhost -tA -c "SELECT 1 FROM pg_database WHERE datname = '$db';"
    if ($exists -ne "1") {
        & $psql -U $SuperuserName -h localhost -v ON_ERROR_STOP=1 -c "CREATE DATABASE $db OWNER $AppRole;"
        Write-Host "Created database $db"
    } else {
        Write-Host "Database $db already exists"
    }
}

Remove-Item Env:\PGPASSWORD

if ($generatedPassword) {
    Write-Host ""
    Write-Host "Generated password for role '$AppRole' (copy into .env now, it will not be shown again):"
    Write-Host $AppPassword
}
Write-Host ""
Write-Host "DATABASE_URL=postgresql+asyncpg://${AppRole}:<password>@localhost:5432/copilot_dev"
Write-Host "TEST_DATABASE_URL=postgresql+asyncpg://${AppRole}:<password>@localhost:5432/copilot_test"
