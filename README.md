# glama-status-mcp

[![FastMCP](https://img.shields.io/badge/FastMCP-3.4.2-blue)](https://github.com/jlowin/fastmcp)
[![Tests](https://img.shields.io/badge/tests-35%20passed-brightgreen)](tests/)
[![Ruff](https://img.shields.io/badge/lint-ruff-green)](https://github.com/astral-sh/ruff)
[![TypeScript](https://img.shields.io/badge/ts-strict-blue)](webapp/tsconfig.json)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Tauri](https://img.shields.io/badge/Tauri-2.0-ffc131)](https://tauri.app)

Daily-refreshed Glama TDQS score tracker for any MCP fleet. Scrapes per-tool grades from glama.ai, stores in SQLite with snapshot history and delta tracking, surfaces via MCP tools, Prefab cards, a 6-page web dashboard, and an LLM-powered chat interface. Tracks repos from any GitHub/Glama author via configurable `config/fleet-repos.json`.

## Quickstart

```bash
git clone https://github.com/sandraschi/glama-status-mcp.git
cd glama-status-mcp

just install
.\start.ps1          # Full stack + browser at :11073
just refresh         # Manual scrape + snapshot
```

## MCP Tools

| Tool | Type | Description |
|------|------|-------------|
| `glama_status` | Portmanteau | 11 ops: list, get, worst_tools, refresh, history, staleness, report, deltas, add_repo, remove_repo, reload_config |
| `glama_scores_summary` | Read-only | Compact grade distribution + per-repo stats |
| `glama_daily_report` | Read-only | Full markdown report: grades, deltas, worst tools, stale repos |
| `glama_agentic_analyze` | Mutating | Uses connected LLM (ctx.sample) to analyze scores and generate actionable fix todos |
| `glama_generate_reports` | Mutating | Writes per-repo markdown fix-todo reports to `reports/` |
| `show_glama_status_card` | Prefab card | Fleet overview dashboard card |
| `show_glama_repo_card` | Prefab card | Per-repo score breakdown card |

## Prompts

- `glama_improvement_plan(repo_name)` -- Per-tool fix priorities with dimension scores
- `glama_fleet_analysis_prompt()` -- Fleet-wide health snapshot for LLM ingestion

## Web Dashboard (6 pages)

| Page | Description |
|------|-------------|
| Dashboard | Hero section, sortable fleet table, click-to-drill repo detail with per-tool 6-dimension bars + Glama links |
| Report | Grade distribution bars, score deltas, worst tools fleet-wide, stale repo flagging |
| Tools | All tools grouped by grade (A-F), each linked to Glama tool page |
| Chat | LLM chat with 4 personalities, provider/model auto-discovery, conversation history, export |
| Help | 5-tab documentation: Overview, Scoring, MCP Tools, REST API, FAQ |
| Settings | GitHub/Glama account config, persisted in localStorage |

## Scored Repos

10 demo repos with actual Glama scores. Add yours via `glama_status(add_repo)` or edit `config/fleet-repos.json`.

| Repo | Grade | Score | Tools |
|------|-------|-------|-------|
| blender-mcp | C | 2.70 | 67 |
| windows-operations-mcp | B | 3.00 | 17 |
| virtualization-mcp | B | 3.06 | 9 |
| worldlabs-mcp | B | 3.38 | 20 |
| robotics-mcp | A | 3.58 | 8 |
| bumi-mcp | A | 3.64 | 2 |
| xkcd-mcp | A | 3.67 | 6 |
| cursor-mcp | A | 3.80 | 6 |
| steam-mcp | A | 3.81 | 14 |
| email-mcp | A | 3.82 | 10 |

## Scoring (Glama TDQS)

Server score = 60% weighted mean + 40% minimum across tools. One low-scoring tool pulls the entire server grade down.

| Grade | Threshold |
|-------|-----------|
| A | >= 3.5 |
| B | >= 3.0 |
| C | >= 2.0 |
| D | >= 1.0 |
| F | < 1.0 |

## Architecture

```
src/glama_status_mcp/
  server.py     -- FastMCP server + FastAPI HTTP + 7 tools + 2 prompts
  scraper.py    -- Async HTML scraper for glama.ai score pages
  database.py   -- SQLite storage + snapshot/delta engine (6 tables)
  models.py     -- Pydantic models + configurable fleet-repos.json loader
  llm.py        -- Glom-On auto-discovery (Ollama/LM Studio/OpenAI)
  config.py     -- Paths, constants
webapp/         -- Vite + React + TailwindCSS v4 (6 pages, 12 components)
native/         -- Tauri 2.0 wrapper + NSIS installer
reports/        -- Generated per-repo markdown fix-todo reports
config/         -- fleet-repos.json (user-editable)
tests/          -- 35 pytest tests + Playwright E2E
```

## Install

| Path | Audience |
|------|----------|
| [INSTALL.md](INSTALL.md) | All installers: Option C (manual), Option D (dev), Options A-B (coming soon) |
| [start.ps1](start.ps1) | One-click: backend + frontend + browser |
| [Native installer](native/target/release/bundle/nsis/) | Tauri NSIS: one download, one shortcut |
| [.mcpb bundle](dist/) | Drag into Claude Desktop |

## Ports

- Backend (FastAPI + MCP HTTP /mcp): 11072
- Frontend (Vite dev): 11073

## Docs

| File | Content |
|------|---------|
| [INSTALL.md](INSTALL.md) | Full install guide |
| [PRD.md](PRD.md) | Product Requirements Document |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [llms.txt](llms.txt) | LLM-facing index |
| [llms-full.txt](llms-full.txt) | LLM-facing full corpus |
