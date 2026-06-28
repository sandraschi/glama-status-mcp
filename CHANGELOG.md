# Changelog

## v0.1.1 (2026-06-28)

### Fixed
- MCP HTTP transport now properly mounted at `/mcp` on FastAPI app
- 57 ruff lint errors resolved (imports, line length, type annotations)
- Grade regex hardened for lxml whitespace quirks
- `start.ps1` no longer uses `cmd.exe /c` for Node.js
- `justfile` no longer uses `cmd.exe /c`; refresh recipe uses `scripts/refresh.py`
- `glama.json` includes `glama_daily_report` tool and `glama_improvement_plan` prompt
- FastMCP `dependencies` kwarg removed (not supported in 3.4+)

### Added
- 35 backend tests (database, scraper, server API)
- Playwright E2E test suite (`webapp/e2e/fleet-audit.spec.ts`)
- Biome TypeScript linting config (`webapp/biome.json`)
- MCPB manifest + 131KB `.mcpb` bundle (`dist/glama-status-mcp-v0.1.1.mcpb`)
- Tauri 2.0 native wrapper with NSIS installer (32.6 MB, `native/`)
- PyInstaller backend spec + `run_server.py` dual-transport entry point
- Prefab UI cards: `show_glama_status_card`, `show_glama_repo_card`
- Glama external links in repo table (score page) and tool breakdown (tool page)
- Dedicated `scripts/refresh.py` for scheduled rescrapes
- Retractable sidebar navigation with Dashboard/Help pages, grade summary, and collapse toggle
- Topbar with breadcrumb view title, Report toggle, grade counts, and Refresh panel

### Changed
- Webapp updated to fleet standards: TailwindCSS v4, Lucide React, Zustand, Framer Motion
- Switched from npm to Bun (`package-lock.json` removed; `bun.lock` expected)
- `bg-gray-950` → `bg-zinc-950` (Zinc palette per fleet standard)
- Animated transitions via Framer Motion (`AnimatePresence`)
- Persistent state via Zustand store
- `scripts/` debug files cleaned (15 removed, 1 rewrite)

## v0.1.0 (2026-06-28)

Initial release.

### Features
- Scraper: fetches Glama score pages for 22 fleet repos, parses per-tool grades and all 6 TDQS dimensions (Purpose, Usage Guidelines, Behavior, Parameters, Conciseness, Completeness)
- SQLite storage with schema for repos, tools, score snapshots, and refresh history
- Delta tracking: snapshots created after each refresh, deltas computed between latest two
- MCP tools: `glama_status` (list/get/worst_tools/refresh/history/staleness/report/deltas), `glama_scores_summary`, `glama_daily_report`
- Web dashboard: Vite + React with sortable fleet table, per-tool dimension breakdown, refresh button, grade distribution
- Polite scraping: descriptive UA, 1s delay, BrightData proxy fallback via env var
- Staleness detection: repos with data >7 days flagged for rescan
- Daily report: markdown format with grade distribution, score changes, worst tools, stale repos

### Infrastructure
- Ports: 11072 (backend), 11073 (frontend)
- Fleet health registered in mcp-central-docs
- justfile with install/serve/web/refresh/lint/smoke recipes
- glama.json, llms.txt, llms-full.txt configured
