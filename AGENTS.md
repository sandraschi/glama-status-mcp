# AGENTS.md  -  glama-status-mcp

Agent protocols for Cursor, Windsurf, Claude Code, and any agentic IDE working in this repo.

## Stack

- **Language:** Python 3.11+, FastMCP >= 3.4.2
- **Package manager:** uv
- **Database:** SQLite via aiosqlite
- **Frontend:** Vite + React + TypeScript
- **Scraping:** httpx + BeautifulSoup + lxml
- **Linting:** Ruff

## Repo layout

```
glama-status-mcp/
├── src/glama_status_mcp/
│   ├── server.py        FastMCP server + FastAPI HTTP mode
│   ├── scraper.py       Async HTML scraper for glama.ai score pages
│   ├── database.py      SQLite storage + delta engine
│   ├── models.py        Pydantic models + fleet repo list
│   └── config.py        Paths, constants, env vars
├── webapp/              Vite + React dashboard
├── data/                SQLite database (gitignored)
├── scripts/             Utility scripts (debug scrapers, scheduler)
├── tests/
├── justfile             just install / serve / web / refresh
├── glama.json
├── llms.txt / llms-full.txt
├── PRD.md
└── CHANGELOG.md
```

## MCP Tools

- `glama_status`  -  Portmanteau: list, get, worst_tools, refresh, history, staleness, report, deltas
- `glama_scores_summary`  -  Grade distribution + per-repo stats
- `glama_daily_report`  -  Full markdown report

## Ports

- Backend: 11072
- Frontend: 11073

## Running

```powershell
just install
just web          # HTTP mode on :11072
just web-frontend # Vite dev on :11073
just refresh      # Manual scrape + snapshot
```

## Database schema

- `repos`  -  Current per-repo scores
- `tools`  -  Per-tool TDQS dimension scores
- `score_snapshots`  -  One row per refresh run
- `score_history`  -  Denormalized per-repo per-snapshot for fast deltas
- `refresh_log`  -  Timestamps and errors per refresh
- `fleet_repos`  -  Tracked repos with author namespace

## Key patterns

- Scraper uses polite HTTP (descriptive UA, 1s delay, BrightData fallback)
- Snapshot + delta engine: every refresh creates a snapshot; deltas compare latest two
- TDQS formula: 60% mean + 40% minimum across tools
- Grade thresholds: A >= 3.5, B >= 3.0, C >= 2.0, D >= 1.0, F < 1.0
