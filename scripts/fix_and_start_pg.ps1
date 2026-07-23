# Restaure pg_hba.conf et demarre PostgreSQL — executer en administrateur
$ErrorActionPreference = 'Stop'
$pgHba = 'C:\Program Files\PostgreSQL\18\data\pg_hba.conf'
$backup = "$pgHba.bak.sghl"
$service = 'postgresql-x64-18'
$psql = 'C:\Program Files\PostgreSQL\18\bin\psql.exe'
$newPassword = 'Postgretheresa'

if (Test-Path $backup) {
    Copy-Item $backup $pgHba -Force
    Write-Host 'Backup pg_hba.conf restaure.'
} else {
    $raw = [System.IO.File]::ReadAllBytes($pgHba)
    if ($raw.Length -ge 3 -and $raw[0] -eq 0xEF -and $raw[1] -eq 0xBB -and $raw[2] -eq 0xBF) {
        [System.IO.File]::WriteAllBytes($pgHba, $raw[3..($raw.Length - 1)])
        Write-Host 'BOM UTF-8 supprime de pg_hba.conf.'
    }
}

Restart-Service $service -Force
Start-Sleep -Seconds 3

# trust temporaire pour reinitialiser le mot de passe
$lines = Get-Content $pgHba
$fixed = $lines | ForEach-Object {
    if ($_ -match '127\.0\.0\.1/32\s+') { 'host    all             all             127.0.0.1/32            trust' }
    elseif ($_ -match '::1/128\s+') { 'host    all             all             ::1/128                 trust' }
    else { $_ }
}
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllLines($pgHba, $fixed, $utf8NoBom)
Restart-Service $service -Force
Start-Sleep -Seconds 3

& $psql -U postgres -h 127.0.0.1 -d postgres -c "ALTER USER postgres PASSWORD '$newPassword';"
$dbExists = & $psql -U postgres -h 127.0.0.1 -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='sghl';"
if ($dbExists -ne '1') {
    & $psql -U postgres -h 127.0.0.1 -d postgres -c "CREATE DATABASE sghl;"
}

# remettre scram-sha-256
$lines2 = Get-Content $pgHba
$secure = $lines2 | ForEach-Object {
    if ($_ -match '127\.0\.0\.1/32\s+trust') { 'host    all             all             127.0.0.1/32            scram-sha-256' }
    elseif ($_ -match '::1/128\s+trust') { 'host    all             all             ::1/128                 scram-sha-256' }
    else { $_ }
}
[System.IO.File]::WriteAllLines($pgHba, $secure, $utf8NoBom)
Restart-Service $service -Force
Start-Sleep -Seconds 3

$env:PGPASSWORD = $newPassword
& $psql -U postgres -h 127.0.0.1 -d sghl -c "SELECT 'PostgreSQL OK' AS status;"
Write-Host 'Configuration PostgreSQL terminee.'
