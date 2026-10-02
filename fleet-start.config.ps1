# Per-repo fleet start config for glama-status-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'glama-status-mcp'
    BackendPort  = 11072
    FrontendPort = 11073
    HealthPath   = '/health'
    WebRoot      = 'webapp'
    Backend = @{
        Kind       = 'module-serve'
        Module     = 'glama_status_mcp'
        ServeArgs  = @('--http', '--port', '11072')
        SyncExtras = @('dev')
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
