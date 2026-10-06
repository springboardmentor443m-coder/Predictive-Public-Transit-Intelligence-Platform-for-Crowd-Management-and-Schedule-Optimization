#requires -Version 5.1
<#
.SYNOPSIS
    Starts (or restarts) the MetroFlow stack and waits until it is ready.

.DESCRIPTION
    Brings up the three Docker containers and blocks until the backend has
    finished loading its models and the frontend dev server is serving, then
    prints the URLs. Safe to run repeatedly - it restarts whatever is already
    running rather than creating duplicates.

.EXAMPLE
    .\restart.ps1
    .\restart.ps1 -Restart     # force-recreate the containers
    .\restart.ps1 -Rebuild     # rebuild images first (slow: downloads ~2GB)
#>

[CmdletBinding()]
param(
    [switch]$Restart,
    [switch]$Rebuild,
    [int]$TimeoutSeconds = 180
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ProjectRoot

function Write-Step($msg)  { Write-Host "==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)    { Write-Host "    OK  $msg" -ForegroundColor Green }
function Write-Warn2($msg) { Write-Host "    !!  $msg" -ForegroundColor Yellow }
function Write-Err($msg)   { Write-Host "    XX  $msg" -ForegroundColor Red }

# ---------------------------------------------------------------- Docker check
Write-Step 'Checking Docker engine...'
$dockerUp = $false
for ($i = 0; $i -lt 40; $i++) {
    $v = docker info --format '{{.ServerVersion}}' 2>&1
    if ($LASTEXITCODE -eq 0 -and $v -match '^\d+\.\d+') {
        Write-Ok "Docker engine $v"
        $dockerUp = $true
        break
    }
    if ($i -eq 0) {
        Write-Warn2 'Docker is not responding - launching Docker Desktop...'
        $exe = "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
        if (Test-Path $exe) { Start-Process $exe } else { Write-Err 'Docker Desktop not found'; exit 1 }
    }
    Start-Sleep -Seconds 5
}
if (-not $dockerUp) { Write-Err "Docker did not become ready"; exit 1 }

# ---------------------------------------------------------------- Bring up
$composeArgs = @('compose', 'up', '-d')
if ($Rebuild)  { $composeArgs += '--build' }
if ($Restart)  { $composeArgs += '--force-recreate' }

Write-Step ("Starting containers: docker " + ($composeArgs -join ' '))
& docker @composeArgs
if ($LASTEXITCODE -ne 0) { Write-Err 'docker compose up failed'; exit 1 }

# ---------------------------------------------------------------- Wait: backend
Write-Step 'Waiting for the backend to load its models...'
$backendReady = $false
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
while ((Get-Date) -lt $deadline) {
    try {
        $r = Invoke-RestMethod 'http://localhost:8000/health' -TimeoutSec 8
        if ($r.status -eq 'healthy') {
            Write-Ok ("backend healthy  (db={0}, model_loaded={1})" -f $r.database, $r.model_loaded)
            $backendReady = $true
            break
        }
    } catch { }
    Start-Sleep -Seconds 3
}
if (-not $backendReady) { Write-Err "Backend not healthy within ${TimeoutSeconds}s"; }

# ---------------------------------------------------------------- Wait: frontend
Write-Step 'Waiting for the frontend dev server...'
$frontReady = $false
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
while ((Get-Date) -lt $deadline) {
    try {
        $r = Invoke-WebRequest 'http://localhost:5173' -UseBasicParsing -TimeoutSec 8
        if ($r.StatusCode -eq 200) { Write-Ok 'frontend serving'; $frontReady = $true; break }
    } catch { }
    Start-Sleep -Seconds 3
}
if (-not $frontReady) { Write-Err "Frontend not serving within ${TimeoutSeconds}s" }

# ---------------------------------------------------------------- Report
Write-Host ''
Write-Step 'Container status'
docker compose ps

Write-Host ''
if ($backendReady -and $frontReady) {
    Write-Host '  MetroFlow is running.' -ForegroundColor Green
    Write-Host ''
    Write-Host '    App    :  http://localhost:5173' -ForegroundColor White
    Write-Host '    API    :  http://localhost:8000' -ForegroundColor White
    Write-Host '    Docs   :  http://localhost:8000/docs' -ForegroundColor White
    Write-Host '    Postgres: localhost:5432  (postgres/postgres, db "metroflow")' -ForegroundColor White
    Write-Host ''
    exit 0
} else {
    Write-Warn2 'Started with problems - see the messages above.'
    Write-Warn2 'Logs:  docker compose logs -f backend'
    exit 1
}