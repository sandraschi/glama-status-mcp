# glama-status-mcp

[![FastMCP](https://img.shields.io/badge/FastMCP-3.4.2-blue)](https://github.com/jlowin/fastmcp)
[![Tests](https://img.shields.io/badge/tests-35%20passed-brightgreen)](tests/)
[![Ruff](https://img.shields.io/badge/lint-ruff-green)](https://github.com/astral-sh/ruff)
[![TypeScript](https://img.shields.io/badge/ts-strict-blue)](webapp/tsconfig.json)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Tauri](https://img.shields.io/badge/Tauri-2.0-ffc131)](https://tauri.app)

Daily-refreshed Glama score tracker for the sandraschi fleet. Scrapes per-tool
TDQS grades from glama.ai, stores in SQLite with snapshot history, surfaces via
MCP tools and a Vite/React web dashboard.

## Quickstart

```bash
git clone https://github.com/sandraschi/glama-status-mcp.git
cd glama-status-mcp

# Install all deps
just install

# Full stack (backend + frontend + browser)
.\start.ps1

# Or step by step
just web          # HTTP backend on :11072
just web-frontend # Vite dev on :11073
just refresh      # Manual scrape + snapshot
```

## MCP Tools

| Tool | Purpose |
|------|---------|
| `glama_status` | Portmanteau: list, get, worst_tools, refresh, history, staleness, report, deltas |
| `glama_scores_summary` | Compact grade distribution and per-repo stats |
| `glama_daily_report` | Full markdown report with deltas, worst tools, stale repos |
| `show_glama_status_card` | Prefab card: fleet overview dashboard |
| `show_glama_repo_card` | Prefab card: per-repo score breakdown |

## Web Dashboard

| Route | Description |
|-------|-------------|
| `/` | Sortable fleet score table |
| `/api/repos` | All repos with per-tool breakdowns |
| `/api/report` | Full daily report JSON |
| `/api/deltas` | Score changes since last snapshot |

## Scored repos (10 of 35 registered on Glama)

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

Server-level score = 60% mean + 40% minimum across tools.
One bad tool pulls the whole server down. Fix the worst tool first.
Grade thresholds: A >= 3.5, B >= 3.0, C >= 2.0, D >= 1.0, F < 1.0.

## Ports

- Backend (FastAPI + MCP HTTP): 11072
- Frontend (Vite dev): 11073

## Docs

| File | Content |
|------|---------|
| [INSTALL.md](INSTALL.md) | Full install guide (Option C: manual, Option D: dev) |
| [PRD.md](PRD.md) | Product Requirements Document |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [llms.txt](llms.txt) | LLM-facing index |
| [llms-full.txt](llms-full.txt) | LLM-facing full corpus |

## Fleet

- Ports registered in `mcp-central-docs/operations/WEBAPP_PORTS.md`
- Project page: `mcp-central-docs/projects/glama-status-mcp/README.md`
- Data sourced from [glama.ai](https://glama.ai/mcp/servers?query=author%3Asandraschi)
