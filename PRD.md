# PRD -- glama-status-mcp

**Product Requirements Document**
**Version:** 0.2
**Date:** 2026-06-29
**Owner:** sandraschi
**Status:** v0.1.1 beta

---

## 1. Problem

Glama.ai provides per-tool TDQS grading for MCP servers, but there is no aggregate view across an entire MCP fleet. Scores must be checked individually on glama.ai per repo. There is no way to:

- See which repos have the worst scores at a glance
- Track score changes over time (deltas)
- Identify which specific tools are dragging a repo's score down
- Get an automated daily summary of fleet health
- Have an LLM analyze scores and generate fixable todos
- Know when a repo's Glama data is stale (needs a release + rescan)

## 2. Solution

glama-status-mcp is a daily-refreshed Glama score tracker that:

1. **Scrapes** glama.ai score pages for any configured fleet repos
2. **Parses** per-tool grades and all 6 TDQS dimensions
3. **Stores** in SQLite with snapshot history for delta tracking
4. **Surfaces** via MCP tools, Prefab cards, and a 6-page web dashboard
5. **Analyzes** via connected LLM (agentic sampling) to generate fix todos
6. **Reports** daily with grade distribution, deltas, worst tools, stale repos
7. **Generates** `reports/` directory with per-repo markdown fix plans for IDE LLM ingestion

## 3. Users

**Primary:** MCP server maintainers who want a single pane of glass showing which repos need docstring improvements to raise Glama scores.

**Secondary:** Anyone who wants to track any MCP server's Glama scores without visiting glama.ai manually.

## 4. Features

### 4.1 MCP Tools (7)
| Tool | Type |
|------|------|
| `glama_status` | Portmanteau: 11 operations |
| `glama_scores_summary` | Read-only grade distribution |
| `glama_daily_report` | Full markdown report |
| `glama_agentic_analyze` | LLM-powered analysis (ctx.sample) |
| `glama_generate_reports` | `reports/` per-repo markdown |
| `show_glama_status_card` | Prefab card: fleet overview |
| `show_glama_repo_card` | Prefab card: per-repo breakdown |

### 4.2 MCP Prompts (2)
- `glama_improvement_plan(repo_name)` -- Per-tool fix priorities
- `glama_fleet_analysis_prompt()` -- Fleet health snapshot

### 4.3 Web Dashboard (6 pages)
- **Dashboard**: Hero + sortable fleet table + repo drill-down
- **Report**: Grade distribution, deltas, worst tools, stale repos
- **Tools**: Fleet-wide tools grouped by grade, Glama links
- **Chat**: LLM chat with personalities, auto-discovered providers
- **Help**: 5-tab documentation (Overview, Scoring, Tools, API, FAQ)
- **Settings**: GitHub account configuration

### 4.4 LLM Integration
- Glom-On auto-discovery: Ollama (11434), LM Studio (1234)
- OpenAI via `OPENAI_API_KEY` env var
- Chat page with conversation history, export, clear
- Agentic analysis via FastMCP `ctx.sample()`

### 4.5 Delta Tracking
- Snapshots created after each successful refresh
- Score changes computed between latest two snapshots
- Highlighted in daily report and web dashboard

### 4.6 Configurable Fleet
- `config/fleet-repos.json` -- user-editable JSON
- Track repos from any Glama author
- Add/remove repos at runtime via MCP tool

## 5. Non-goals

- Not a Glama submission tool (use glama.ai directly)
- Not a docstring editor (fixes happen in each repo's own PRs)
- Not a CI gate (does not block releases based on scores)
- Not a replacement for Glama's own scoring infrastructure

## 6. Architecture

```
glama-status-mcp/
├── src/glama_status_mcp/
│   ├── server.py    -- FastMCP + FastAPI + 7 tools + 2 prompts
│   ├── scraper.py   -- Async HTML scraper
│   ├── database.py  -- SQLite (6 tables) + delta engine
│   ├── models.py    -- Pydantic models + config loader
│   ├── llm.py       -- Glom-On discovery + chat client
│   ├── reporting.py -- per-repo markdown report generator
│   └── config.py    -- Paths, constants
├── webapp/          -- Vite + React + TailwindCSS v4
│   ├── src/
│   │   ├── components/  (12 components)
│   │   ├── store.ts, types.ts
│   │   └── index.css
│   └── e2e/         -- Playwright tests
├── native/          -- Tauri 2.0 + NSIS installer
├── config/          -- fleet-repos.json (user-editable)
├── reports/         -- Generated per-repo fix-todo reports
├── data/            -- SQLite database (gitignored)
├── tests/           -- 35 pytest tests
├── mcpb/            -- MCPB bundle
├── scripts/         -- refresh.py, smoke.py, scheduler
└── dist/            -- Build artifacts
```

Ports: 11072 (backend), 11073 (frontend).

## 7. Success Metrics

- All configured repos scored and visible in dashboard
- Delta tracking shows meaningful change over time
- Worst tools identified and linked to Glama for inspection
- LLM analysis produces actionable fix lists
- Config works for any Glama author, not just one account
