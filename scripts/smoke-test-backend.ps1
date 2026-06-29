$frozen = "D:\Dev\repos\glama-status-mcp\dist\glama-status-mcp-backend.exe"
$testPort = 11999
$env:MCP_PORT = "$testPort"
$env:MCP_HOST = "127.0.0.1"
$proc = Start-Process -FilePath $frozen -NoNewWindow -PassThru -RedirectStandardError "$env:TEMP\pyi-crash.log"
Start-Sleep -Seconds 8
if ($proc.HasExited) {
    Write-Host "CRASHED (exit $($proc.ExitCode)):"
    Get-Content "$env:TEMP\pyi-crash.log"
} else {
    Write-Host "SMOKE PASSED"
    $proc.Kill()
}
Remove-Item env:MCP_PORT -ErrorAction SilentlyContinue
Remove-Item env:MCP_HOST -ErrorAction SilentlyContinue
