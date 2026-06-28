# Changelog

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
