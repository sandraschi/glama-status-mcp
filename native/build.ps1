$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$RepoName = "glama-status-mcp"
$Triple = "x86_64-pc-windows-msvc"
$ResourceDir = "$PSScriptRoot\resources"
$DevDir = "$PSScriptRoot\binaries"
$BackendPort = 11072
New-Item -ItemType Directory -Force -Path $ResourceDir, $DevDir | Out-Null

Write-Host "=== ${RepoName} Tauri Release Build ===" -ForegroundColor Cyan

# Step 0: Verify API_BASE matches backend port
Write-Host "-> [0/5] Verifying API_BASE port..." -ForegroundColor Yellow
$viteConfig = Join-Path $Root "webapp\vite.config.ts"
if (Test-Path $viteConfig) {
    $content = Get-Content $viteConfig -Raw
    if ($content -match "127\.0\.0\.1:(\d+)") {
        $apiPort = [int]$Matches[1]
        if ($apiPort -ne $BackendPort) {
            throw "vite.config.ts proxy points to port $apiPort but backend serves on $BackendPort."
        }
        Write-Host "  Vite proxy port: $apiPort (matches backend) OK" -ForegroundColor Green
    }
}

# Step 1: Frontend build
Write-Host "-> [1/5] Building frontend..." -ForegroundColor Yellow
$frontend = Join-Path $Root "webapp"
Push-Location $frontend

# TypeScript lint gate
Write-Host "  tsc --noEmit..." -ForegroundColor Gray
$tscOut = npx tsc --noEmit 2>&1
$tscExit = $LASTEXITCODE
if ($tscExit -ne 0) {
    Write-Host "  TypeScript compilation FAILED" -ForegroundColor Red
    Write-Host $tscOut
    throw "TypeScript compilation failed"
}

Remove-Item "dist" -Recurse -Force -ErrorAction SilentlyContinue
npm run build
if ($LASTEXITCODE -ne 0) { throw "Frontend build failed" }
Pop-Location

# Step 2: PyInstaller backend
Write-Host "-> [2/5] PyInstaller backend..." -ForegroundColor Yellow
$specFile = "$Root\${RepoName}-backend.spec"
if (-not (Test-Path $specFile)) {
    throw "Spec file not found: $specFile"
}

Push-Location $Root

# Patch fastmcp metadata fallback
$fm = "$Root\.venv\Lib\site-packages\fastmcp\__init__.py"
if (Test-Path $fm) {
    $c = Get-Content $fm -Raw
    if ($c -match 'except PackageNotFoundError:\s+    __version__ = _version\("fastmcp"\)') {
        $c = $c -replace 'except PackageNotFoundError:\s+    __version__ = _version\("fastmcp"\)',
                         'except PackageNotFoundError:
    try:
        __version__ = _version("fastmcp")
    except PackageNotFoundError:
        __version__ = "0.0.0"'
        Set-Content $fm -Value $c -Encoding utf8
        Write-Host "  Patched fastmcp metadata fallback" -ForegroundColor Yellow
    }
}

$pyiExe = "$Root\.venv\Scripts\pyinstaller.exe"
if (-not (Test-Path $pyiExe)) {
    Write-Host "  Installing pyinstaller in project venv..." -ForegroundColor Yellow
    uv add --dev pyinstaller
}

# Kill zombie backend processes before removing stale exe
Get-Process "$RepoName-backend" -ErrorAction SilentlyContinue | Stop-Process -Force
taskkill /F /IM "$RepoName-backend.exe" /T 2>$null
Start-Sleep 2
Remove-Item "$Root\dist\$RepoName-backend.exe" -Force -ErrorAction SilentlyContinue
& $pyiExe "$specFile" --clean --noconfirm
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

# Smoke-test frozen binary
$frozenExe = "$Root\dist\$RepoName-backend.exe"
Write-Host "  Smoke-testing frozen binary..." -ForegroundColor Yellow
$testPort = 11999
$env:MCP_PORT = "$testPort"
$env:MCP_HOST = "127.0.0.1"
$testProc = Start-Process -FilePath $frozenExe -NoNewWindow -PassThru `
    -RedirectStandardError "$Root\dist\pyi-crash.log"
Start-Sleep -Seconds 5
if ($testProc.HasExited) {
    $crash = Get-Content "$Root\dist\pyi-crash.log" -Raw
    throw "Frozen binary crashed on launch (exit $($testProc.ExitCode)):`n$crash"
}
$testProc.Kill(); $testProc.Dispose()
Remove-Item "$Root\dist\pyi-crash.log" -Force -ErrorAction SilentlyContinue
Remove-Item env:MCP_PORT -ErrorAction SilentlyContinue
Remove-Item env:MCP_HOST -ErrorAction SilentlyContinue
Write-Host "  Frozen binary smoke test PASSED" -ForegroundColor Green

Pop-Location

# Step 3: Embed backend in Tauri resources
Write-Host "-> [3/5] Embedding backend..." -ForegroundColor Yellow
$src = "$Root\dist\$RepoName-backend.exe"
if (-not (Test-Path $src)) { throw "Backend exe not found: $src" }

$sizeMB = (Get-Item $src).Length / 1MB
if ($sizeMB -lt 5) {
    throw "Backend exe is only $([math]::Round($sizeMB, 1)) MB -- PyInstaller produced broken binary"
}
Copy-Item $src "$ResourceDir\$RepoName-backend.exe" -Force
Copy-Item $src "$DevDir\$RepoName-backend-$Triple.exe" -Force
Write-Host "  Backend exe: $sizeMB MB" -ForegroundColor Green

# Step 4: Tauri NSIS bundle
Write-Host "-> [4/5] Tauri NSIS bundle..." -ForegroundColor Yellow
Push-Location $PSScriptRoot
$env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
npx @tauri-apps/cli build --bundles nsis
if ($LASTEXITCODE -ne 0) { throw "Tauri build failed" }
Pop-Location

# Stage to repo dist/
$distDir = Join-Path $Root "dist"
New-Item -ItemType Directory -Force -Path $distDir | Out-Null
$nsisDir = "$PSScriptRoot\target\release\bundle\nsis"
if (Test-Path $nsisDir) {
    Copy-Item "$nsisDir\*-setup.exe" "$distDir\" -Force
}

Write-Host "=== Build complete ===" -ForegroundColor Green
Write-Host "Ship: $nsisDir\*.exe"
