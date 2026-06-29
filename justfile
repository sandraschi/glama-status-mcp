set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]

# glama-status-mcp justfile
default:
    just --list

# Install all dependencies (core + dev + web)
install:
    uv sync --extra dev --extra web

# Run MCP server (stdio)
serve:
    uv run python -m glama_status_mcp

# Run web backend on port 11072
web:
    uv run python -m glama_status_mcp --http --port 11072

# Run web frontend (Vite dev on 11073)
web-frontend:
    Set-Location '{{justfile_directory()}}\webapp' ; npx vite --port 11073 --host

# Run full stack (backend + frontend + auto-open)
web-dev:
    powershell.exe -NoProfile -File '{{justfile_directory()}}\start.ps1'

# Refresh all scores from Glama (creates a snapshot)
refresh:
    uv run python scripts/refresh.py

# Lint
lint:
    uv run ruff check src/

# Run tests
test:
    uv run pytest tests/ -q

# CI checks (matching CI workflow)
ci: lint test

# Format check
format-check:
    uv run ruff format --check src/

# Fix formatting
format:
    uv run ruff format src/

# Build frontend for production
build-web:
    Set-Location '{{justfile_directory()}}\webapp' ; npx vite build

# Smoke test
smoke:
    uv run python -c "from glama_status_mcp.database import init_db, seed_fleet, get_all_repo_scores; from glama_status_mcp.models import FLEET_REPOS; import sys; init_db(); seed_fleet(FLEET_REPOS); repos=get_all_repo_scores(); print(f'DB ready: {len(repos)} repos in database')"

# Create daily scheduled task
schedule-daily:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File '{{justfile_directory()}}\scripts\register-daily-refresh.ps1'

# Packages
# Bundle for Claude Desktop (MCPB)
mcpb-pack:
    npx @anthropic-ai/mcpb pack . dist/glama-status-mcp-v0.1.1.mcpb

# Build the PyInstaller backend .exe and copy to Tauri resources
build-sidecar:
    pwsh -NoProfile -File '{{justfile_directory()}}\native\build.ps1'

# Build the Tauri NSIS desktop installer (full pipeline)
build-native:
    pwsh -NoProfile -File '{{justfile_directory()}}\native\build.ps1'
