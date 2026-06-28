# glama-status-mcp

Daily-refreshed Glama score tracker for the sandraschi fleet. Scrapes per-tool TDQS grades from glama.ai, stores in SQLite, surfaces via MCP tools and a web dashboard. Tracks deltas between snapshots, generates daily reports, and flags stale repos needing rescan.

## Quickstart

```bash
just install
just web          # HTTP backend on :11072
just web-frontend # Vite dev on :11073
just web-dev      # Full stack
just refresh      # Manual scrape + snapshot
```

## MCP Tools

| Tool | Purpose |
|------|---------|
| `glama_status` | Portmanteau: list, get, worst_tools, refresh, history, staleness, report, deltas |
| `glama_scores_summary` | Compact grade distribution and per-repo stats |
| `glama_daily_report` | Full markdown report with deltas, worst tools, stale repos |

## Web Dashboard

| Route | Description |
|-------|-------------|
| `/` | Sortable fleet score table |
| `/api/repos` | All repos with per-tool breakdowns |
| `/api/repos/{name}` | Single repo tool breakdown |
| `/api/report` | Full daily report JSON |
| `/api/deltas` | Score changes since last snapshot |
| `/api/refresh` (POST) | Trigger rescrape + snapshot |
| `/api/worst-tools` | Lowest-scoring tools fleet-wide |

## How it works

1. **Scraper** fetches `glama.ai/mcp/servers/{author}/{repo}/score` pages
2. **Parser** extracts per-tool grades, 6 TDQS dimension scores, coherence, and maintenance data
3. **SQLite** stores current scores + snapshot history for delta tracking
4. **Daily refresh** via Scheduled Task or `just refresh` creates a new snapshot
5. **Delta engine** compares latest two snapshots to show changes

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

25 more registered on Glama but not yet analyzed (page exists, no tools).

## Scoring (Glama TDQS)

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Purpose Clarity | 25% | First sentence states what the tool does |
| Usage Guidelines | 20% | When to / not to call, preconditions |
| Behavioral Transparency | 20% | Returns, side effects, error conditions |
| Parameter Semantics | 15% | Every param: type, values, what it affects |
| Conciseness & Structure | 10% | Not a wall of text, not a one-liner |
| Contextual Completeness | 10% | Enough context to use without reading source |

Server-level = 60% mean + 40% minimum  -  one bad tool pulls the whole score down.

## Ports

- Backend (FastAPI + MCP HTTP): 11072
- Frontend (Vite dev): 11073
