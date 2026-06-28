# Install

## Prerequisites

| Tool | When needed | Windows |
|------|-------------|---------|
| Git | C, D | `winget install Git.Git` |
| uv | C, D | `winget install astral-sh.uv` |
| Node.js | C (frontend) | `winget install OpenJS.NodeJS` |
| Claude Desktop | C | [claude.ai/download](https://claude.ai/download) |

After winget: close and reopen terminal for PATH to refresh.

## Quickstart

```powershell
git clone https://github.com/sandraschi/glama-status-mcp.git
cd glama-status-mcp
.\start.ps1
```

Opens browser at http://127.0.0.1:11073.

## Option A -- Drag and Drop (Coming Soon)

MCPB bundles are not yet published. When available, download the `.mcpb`
file from GitHub Releases and drag into Claude Desktop. No Python, uv, git,
or Node required.

## Option B -- mcpb CLI (Coming Soon)

Requires Node.js via winget. The `.mcpb` bundle will be installable via:

```powershell
npx @anthropic-ai/mcpb install https://github.com/sandraschi/glama-status-mcp
```

## Option C -- Manual Configuration

### 1. Clone and install

```powershell
git clone https://github.com/sandraschi/glama-status-mcp.git
cd glama-status-mcp
uv sync --extra dev --extra web
```

### 2. Register in Claude Desktop

Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "glama-status": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\path\\to\\glama-status-mcp",
        "run",
        "glama-status-mcp"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### 3. Start web dashboard (optional)

```powershell
.\start.ps1
```

## Option D -- Developer Mode

```powershell
git clone https://github.com/sandraschi/glama-status-mcp.git
cd glama-status-mcp
uv sync --extra dev --extra web

# Backend
uv run python -m glama_status_mcp --http --port 11072

# Frontend (separate terminal)
cd webapp
npm install
npx vite --port 11073 --host

# Lint
uv run ruff check src/

# Tests
uv run pytest tests/ -v
```

## Ports

- Backend (FastAPI + MCP HTTP `/mcp`): 11072
- Frontend (Vite dev): 11073

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GLAMA_SCRAPE_TIMEOUT` | 30 | HTTP timeout per scrape (seconds) |
| `GLAMA_SCRAPE_DELAY` | 1.0 | Delay between scrapes (seconds) |
| `GLAMA_AUTHOR` | sandraschi | Glama author namespace |
| `GLAMA_USE_BRIGHTDATA` | (unset) | Set to `1` to proxy via BrightData |
| `GLAMA_BRIGHTDATA_TOKEN` | (unset) | BrightData proxy auth token |

## Daily Refresh

Register a Windows Scheduled Task to refresh scores daily at 6:00 AM:

```powershell
just schedule-daily
```
