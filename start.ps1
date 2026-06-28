param([switch]$Headless, [switch]$BackendOnly, [switch]$NoBrowser)
$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $PSCommandPath
$BackendPort = 11072
$FrontendPort = 11073

# Port zombie clearing
Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

# Start backend via Start-Job
$BackendJob = Start-Job -Name "glama-backend" -ScriptBlock {
    param($Root, $Port)
    Set-Location $Root
    uv run python -m glama_status_mcp --http --port $Port
} -ArgumentList $ScriptRoot, $BackendPort

# Readiness poll
Write-Host "Waiting for backend on port $BackendPort..."
for ($i = 0; $i -lt 30; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$BackendPort/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($r.StatusCode -eq 200) { Write-Host "Backend ready."; break }
    } catch {}
    Start-Sleep 1
}

if ($BackendOnly) {
    Write-Host "Backend running on http://127.0.0.1:$BackendPort"
    Wait-Job $BackendJob | Out-Null
    return
}

# Install frontend deps if needed
$WebRoot = Join-Path $ScriptRoot "webapp"
if (-not (Test-Path (Join-Path $WebRoot "node_modules"))) {
    Write-Host "Installing frontend dependencies..."
    Push-Location $WebRoot
    npm install
    Pop-Location
}

# Start frontend
Start-Process -NoNewWindow -FilePath "npx" -ArgumentList "vite --port $FrontendPort --host" -WorkingDirectory $WebRoot

# Auto-open browser
if (-not $NoBrowser) {
    Start-Sleep 3
    Start-Process "http://127.0.0.1:$FrontendPort"
}

Write-Host "glama-status-mcp running:"
Write-Host "  Backend: http://127.0.0.1:$BackendPort"
Write-Host "  Frontend: http://127.0.0.1:$FrontendPort"

# Keep-alive
while ($true) {
    if ($BackendJob.State -eq "Completed" -or $BackendJob.State -eq "Failed") {
        Receive-Job $BackendJob
        break
    }
    Start-Sleep 2
}
