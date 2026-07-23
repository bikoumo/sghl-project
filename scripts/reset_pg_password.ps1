# Requiert PowerShell en administrateur
$ErrorActionPreference = 'Stop'
$pgData = 'C:\Program Files\PostgreSQL\18\data'
$pgHba = Join-Path $pgData 'pg_hba.conf'
$psql = 'C:\Program Files\PostgreSQL\18\bin\psql.exe'
$service = 'postgresql-x64-18'
$newPassword = 'Postgretheresa'
$backup = "$pgHba.bak.sghl"

if (-not (Test-Path $pgHba)) {
    Write-Error "pg_hba.conf introuvable: $pgHba"
}

Copy-Item $pgHba $backup -Force
$content = Get-Content $pgHba -Raw
$content = $content -replace '127\.0\.0\.1/32\s+scram-sha-256', '127.0.0.1/32            trust'
$content = $content -replace '::1/128\s+scram-sha-256', '::1/128                 trust'
Set-Content -Path $pgHba -Value $content -Encoding UTF8

Restart-Service $service -Force
Start-Sleep -Seconds 2

& $psql -U postgres -h 127.0.0.1 -d postgres -c "ALTER USER postgres PASSWORD '$newPassword';"
& $psql -U postgres -h 127.0.0.1 -d postgres -c "SELECT 1 FROM pg_database WHERE datname='sghl';" | Out-Null
if ($LASTEXITCODE -ne 0) { }
$dbExists = & $psql -U postgres -h 127.0.0.1 -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='sghl';"
if ($dbExists -ne '1') {
    & $psql -U postgres -h 127.0.0.1 -d postgres -c "CREATE DATABASE sghl;"
}

Copy-Item $backup $pgHba -Force
Restart-Service $service -Force
Start-Sleep -Seconds 2

$env:PGPASSWORD = $newPassword
& $psql -U postgres -h 127.0.0.1 -d sghl -c "SELECT current_database();"
Write-Host "Mot de passe PostgreSQL reinitialise avec succes."
