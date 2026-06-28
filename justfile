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
    Set-Location '{{justfile_directory()}}\webapp' && npx vite --port 11073 --host

# Run full stack (backend + frontend)
web-dev:
    Start-Job -Name gs-backend { Set-Location '{{justfile_directory()}}'; uv run python -m glama_status_mcp --http --port 11072 }
    Start-Sleep 3
    Set-Location '{{justfile_directory()}}\webapp' && npx vite --port 11073 --host

# Refresh all scores from Glama
refresh:
    uv run python -c "import asyncio; from glama_status_mcp.scraper import scrape_repo; from glama_status_mcp.database import init_db, seed_fleet, upsert_repo_score; from glama_status_mcp.models import FLEET_REPOS; import asyncio; init_db(); seed_fleet(FLEET_REPOS); async def go(): import asyncio; successes=0; total=len(FLEET_REPOS); import sys; sys.stdout.write(f'Scraping {total} repos...\n'); r=await asyncio.gather(*[scrape_repo(r.name,r.glama_author) for r in FLEET_REPOS], return_exceptions=True); [upsert_repo_score(s) for s in r if isinstance(s, type(None)) is False and not isinstance(s, Exception)]; successes=sum(1 for s in r if isinstance(s, type(None)) is False and not isinstance(s, Exception)); print(f'Done: {successes}/{total}'); asyncio.run(go())"

# Lint
lint:
    uv run ruff check src/

# Format check
format-check:
    uv run ruff format --check src/

# Build frontend
build-web:
    Set-Location '{{justfile_directory()}}\webapp' && npm install && npm run build

# Smoke test
smoke:
    uv run python -c "from glama_status_mcp.database import init_db, seed_fleet, get_all_repo_scores; from glama_status_mcp.models import FLEET_REPOS; import sys; init_db(); seed_fleet(FLEET_REPOS); repos=get_all_repo_scores(); sys.stdout.write(f'DB ready: {len(repos)} repos in database\n')"
