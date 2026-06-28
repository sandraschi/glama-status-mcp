<#
.SYNOPSIS
    Register a daily Scheduled Task to refresh Glama scores at 6:00 AM.
.DESCRIPTION
    Creates a task named "glama-status-mcp-refresh" that runs `just refresh`
    in the repo root daily at 6:00 AM. Skips if the task already exists.
.PARAMETER Force
    Overwrite existing task.
.EXAMPLE
    .\scripts\register-daily-refresh.ps1
    .\scripts\register-daily-refresh.ps1 -Force
#>
[CmdletBinding()]
param([switch]$Force)

$ErrorActionPreference = "Stop"
$TaskName = "glama-status-mcp-refresh"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)

# Resolve just.exe
$justExe = (Get-Command "just" -ErrorAction SilentlyContinue).Source
if (-not $justExe) {
    $justCandidates = @(
        "$env:LOCALAPPDATA\Microsoft\WinGet\Links\just.exe",
        "C:\Program Files\just\just.exe",
        "$env:USERPROFILE\.local\bin\just.exe"
    )
    $justExe = $justCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}
if (-not $justExe) { throw "just not found. Install via winget: winget install Casey.Just" }

$action = New-ScheduledTaskAction -Execute "$justExe" -Argument "refresh" -WorkingDirectory $RepoRoot
$trigger = New-ScheduledTaskTrigger -Daily -At "06:00"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    if (-not $Force) {
        Write-Host "Task '$TaskName' already exists. Use -Force to overwrite."
        return
    }
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -RunLevel Limited -User $env:USERNAME
Write-Host "Registered: $TaskName (daily at 6:00 AM)"
