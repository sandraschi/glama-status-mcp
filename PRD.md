# PRD  -  glama-status-mcp

**Product Requirements Document**
**Version:** 0.1
**Date:** 2026-06-28
**Owner:** sandraschi
**Status:** v0.1.0  -  initial release

---

## 1. Problem

Glama.ai provides per-tool TDQS grading for MCP servers, but there is no aggregate view across the entire sandraschi fleet. Scores must be checked individually on glama.ai per repo. There is no way to:

- See which repos have the worst scores at a glance
- Track score changes over time
- Identify which specific tools are dragging a repo's score down
- Get an automated daily summary of fleet health
- Know when a repo's Glama data is stale (needs a release + rescan)

## 2. Solution

glama-status-mcp is a daily-refreshed Glama score tracker that:

1. **Scrapes** glama.ai score pages for all 22 fleet repos
2. **Parses** per-tool grades and all 6 TDQS dimensions (Purpose, Usage, Behavior, Parameters, Conciseness, Completeness)
3. **Stores** in SQLite with snapshot history for delta tracking
4. **Surfaces** via MCP tools and a Vite/React web dashboard
5. **Reports** daily with grade distribution, changes since last snapshot, worst tools fleet-wide, and stale repos

## 3. Users

**Primary:** Sandra (fleet owner). Needs a single pane of glass showing which repos need docstring improvements to raise Glama scores. Secondary: any fleet contributor who wants to see their repo's grading breakdown without visiting glama.ai.

## 4. Features

### 4.1 MCP Tools
- `glama_status`  -  portmanteau: list, get, worst_tools, refresh, history, staleness, report, deltas
- `glama_scores_summary`  -  grade distribution and per-repo fast stats
- `glama_daily_report`  -  full markdown report with deltas, tables, worst tools

### 4.2 Web Dashboard
- Sortable fleet table (by grade, score, staleness)
- Per-tool drilldown with dimension bar charts
- Refresh trigger with progress
- Color-coded grade indicators

### 4.3 Delta Tracking
- Snapshots created after each successful refresh
- Score changes computed between latest two snapshots
- Highlighted in daily report and available via `glama_status(operation="deltas")`

### 4.4 Daily Refresh
- Scheduled Task runs `glama_status(operation="refresh")` daily
- Polite scraping with 1s delay between requests
- BrightData proxy fallback via `GLAMA_USE_BRIGHTDATA=1`
- Respects robots.txt (own repos, low volume)

## 5. Non-goals

- Not a Glama submission tool (use glama.ai directly)
- Not a docstring editor (fixes happen in each repo's own PRs)
- Not a CI gate (does not block releases based on scores)

## 6. Architecture

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
├── tests/
└── scripts/
```

Ports: 11072 (backend), 11073 (frontend).

## 7. Success Metrics

- All 22 fleet repos scored and visible in the dashboard
- Delta tracking shows meaningful week-over-week improvements
- Worst tools identified and fixed (repo maintainers act on the data)
- Zero scraping errors for repos that have Glama score pages
