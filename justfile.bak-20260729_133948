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
    Set-Location '{{justfile_directory()}}\webapp' && cmd.exe /c npx vite --port 11073 --host

# Run full stack (backend + frontend + auto-open)
web-dev:
    powershell.exe -NoProfile -File '{{justfile_directory()}}\start.ps1'

# Refresh all scores from Glama (creates a snapshot)
refresh:
    uv run python -c "import asyncio; from glama_status_mcp.database import init_db, seed_fleet, upsert_repo_score, create_snapshot, log_refresh_start, log_refresh_end; from glama_status_mcp.models import FLEET_REPOS; from glama_status_mcp.scraper import scrape_repo; import sys; init_db(); seed_fleet(FLEET_REPOS); import time; log_id=log_refresh_start(); errors=[]; s=f=0; total=len(FLEET_REPOS); print(f'Scraping {total} repos...'); async def go(): global s,f; import asyncio; [await asyncio.sleep(0) for _ in range(1)]; r=[await scrape_repo(x.name,x.glama_author) for x in FLEET_REPOS]; [upsert_repo_score(v) for v in r if v and not isinstance(v,Exception)]; global s,f; s=sum(1 for v in r if v and not isinstance(v,Exception)); f=sum(1 for v in r if v is None or isinstance(v,Exception)); [errors.append(f'{FLEET_REPOS[i].name}: {r[i]}') for i in range(len(r)) if isinstance(r[i],Exception)]; asyncio.run(go()); snap=create_snapshot(log_id) if s>0 else None; log_refresh_end(log_id,total,s,f,errors[:10]); print(f'Done: {s}/{total}, snapshot={snap}')"

# Lint
lint:
    uv run ruff check src/

# Format check
format-check:
    uv run ruff format --check src/

# Fix formatting
format:
    uv run ruff format src/

# Build frontend for production
build-web:
    Set-Location '{{justfile_directory()}}\webapp' && cmd.exe /c npm install && cmd.exe /c npx vite build

# Smoke test
smoke:
    uv run python -c "from glama_status_mcp.database import init_db, seed_fleet, get_all_repo_scores; from glama_status_mcp.models import FLEET_REPOS; import sys; init_db(); seed_fleet(FLEET_REPOS); repos=get_all_repo_scores(); print(f'DB ready: {len(repos)} repos in database')"

# Create daily scheduled task
schedule-daily:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File '{{justfile_directory()}}\scripts\register-daily-refresh.ps1'
