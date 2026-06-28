<#
.SYNOPSIS
    Start glama-status-mcp: backend + frontend with auto-open browser.
.DESCRIPTION
    Installs uv/Node.js if missing (via winget), syncs Python deps, starts the
    FastAPI backend on port 11072, waits for health, then starts the Vite
    frontend on port 11073 and opens the browser.
.PARAMETER Headless
    Skip browser auto-open.
.PARAMETER BackendOnly
    Start only the backend, no frontend.
.PARAMETER NoBrowser
    Skip browser auto-open (alias for Headless).
.EXAMPLE
    .\start.ps1
    .\start.ps1 -BackendOnly
#>
[CmdletBinding()]
param(
    [switch]$Headless,
    [switch]$BackendOnly,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $PSCommandPath
Set-Location $ScriptRoot
$BackendPort = 11072
$FrontendPort = 11073
$RepoName = "glama-status-mcp"

# ── Helper: require a winget-installable command ──
function Require-Command {
    param([string]$Command, [string]$WingetId, [string]$CheckArg = "--version")
    $exe = Get-Command $Command -ErrorAction SilentlyContinue
    if (-not $exe) {
        Write-Host "Installing $Command via winget..."
        winget install --id $WingetId --silent --accept-package-agreements --accept-source-agreements 2>&1 | Out-Null
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
                    [System.Environment]::GetEnvironmentVariable("PATH", "User")
        $exe = Get-Command $Command -ErrorAction SilentlyContinue
        if (-not $exe) { throw "Failed to install $Command via winget." }
    }
    Write-Host "  $Command $(& $exe $CheckArg 2>&1 | Select-Object -First 1)"
}

# ── Prerequisites ──
Write-Host "=== $RepoName ==="
Require-Command -Command "uv" -WingetId "astral-sh.uv"
Require-Command -Command "node" -WingetId "OpenJS.NodeJS"

# -- Python deps --
if (-not (Test-Path (Join-Path $ScriptRoot ".venv"))) {
    Write-Host "Installing Python dependencies..."
}
$prevEA = $ErrorActionPreference
$ErrorActionPreference = "Continue"
uv sync --extra dev --extra web 2>&1 | Out-Null
$ErrorActionPreference = $prevEA

# -- Import smoke test --
Write-Host "Verifying Python imports..."
$prevEA2 = $ErrorActionPreference
$ErrorActionPreference = "Continue"
uv run python scripts/smoke.py 2>&1
$ErrorActionPreference = $prevEA2

# ── Port zombie clearing ──
Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

# ── Start backend ──
$BackendJob = Start-Job -Name "glama-backend" -ScriptBlock {
    param($Root, $Port)
    Set-Location $Root
    uv run python -m glama_status_mcp --http --port $Port
} -ArgumentList $ScriptRoot, $BackendPort

Write-Host "Waiting for backend on port $BackendPort..."
$backendReady = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$BackendPort/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($r.StatusCode -eq 200) { $backendReady = $true; break }
    } catch {}
    Start-Sleep 1
}
if (-not $backendReady) {
    Write-Warning "Backend health check timed out after 30s. Check logs above."
}

Write-Host "Backend: http://127.0.0.1:$BackendPort"

if ($BackendOnly) {
    Wait-Job $BackendJob | Out-Null
    return
}

# ── Frontend ──
$WebRoot = Join-Path $ScriptRoot "webapp"
if (-not (Test-Path (Join-Path $WebRoot "node_modules"))) {
    Write-Host "Installing frontend dependencies..."
    Push-Location $WebRoot
    $prevEA3 = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    npm install 2>&1 | Out-Null
    $ErrorActionPreference = $prevEA3
    Pop-Location
}

$frontendJob = Start-Job -Name "glama-frontend" -ScriptBlock {
    param($Root, $Port)
    Set-Location $Root
    npx vite --port $Port --host
} -ArgumentList $WebRoot, $FrontendPort

Write-Host "Frontend: http://127.0.0.1:$FrontendPort"

# ── Poll-and-open pattern ──
$pollScript = @"
for (`$i = 0; `$i -lt 60; `$i++) {
    try {
        `$null = Invoke-WebRequest -Uri 'http://127.0.0.1:$FrontendPort' -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        Start-Process 'http://127.0.0.1:$FrontendPort'
        exit
    } catch { Start-Sleep -Seconds 1 }
}
"@

if (-not $Headless -and -not $NoBrowser) {
    Write-Host "Opening browser..."
    Start-Job -ScriptBlock { param($s) iex $s } -ArgumentList $pollScript | Out-Null
}

# ── Keep-alive ──
try {
    while ($true) {
        if ($BackendJob.State -eq "Completed" -or $BackendJob.State -eq "Failed") {
            Receive-Job $BackendJob
            break
        }
        Start-Sleep 2
    }
} finally {
    Stop-Job $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $BackendJob -ErrorAction SilentlyContinue
}
