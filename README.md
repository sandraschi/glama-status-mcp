# glama-status-mcp

[![FastMCP](https://img.shields.io/badge/FastMCP-3.4.2-blue)](https://github.com/jlowin/fastmcp)
[![Tests](https://img.shields.io/badge/tests-35%20passed-brightgreen)](tests/)
[![Ruff](https://img.shields.io/badge/lint-ruff-green)](https://github.com/astral-sh/ruff)
[![Tauri](https://img.shields.io/badge/Tauri-2.0-ffc131)](https://tauri.app)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Daily-refreshed Glama TDQS score tracker for any MCP fleet. Scrapes per-tool docstring quality grades from glama.ai, stores in SQLite with snapshot history and delta tracking, surfaces via MCP tools and a 6-page web dashboard.

## Features

- **Auto-discover** all your repos on Glama -- one command populates your fleet
- **Per-tool 6-dimension breakdown** -- Purpose, Usage, Behavior, Parameters, Conciseness, Completeness
- **Snapshot delta tracking** -- score changes between refreshes, stale repo detection
- **LLM-powered analysis** -- connected chat page and agentic tool (ctx.sample) to generate fixable todos
- **Prefab UI cards** for in-chat fleet overview and per-repo breakdown
- **6-page web dashboard** -- Dashboard, Report, Tools, Chat, Help, Settings
- **Tauri 2.0 NSIS installer** -- single download, embedded backend, no Python required
- **Track any author** -- configure `config/fleet-repos.json` to monitor any Glama user's servers

## Quick Install

**Drag into Claude Desktop** -- download [glama-status-mcp-v0.1.1.mcpb](dist/glama-status-mcp-v0.1.1.mcpb) and drop it onto the window. MCP tools only (no webapp).

For the web dashboard or native desktop app, see [INSTALL.md](INSTALL.md).

## What You Can Do

```
# Check fleet health
glama_status(operation="list")
glama_status(operation="report")

# Deep dive a repo
glama_status(operation="get", repo_name="email-mcp")
show_glama_repo_card(repo_name="blender-mcp")

# LLM-powered analysis
glama_agentic_analyze(repo_name="email-mcp")
glama_agentic_analyze()  # whole fleet

# Generate fix-todo reports
glama_generate_reports(repo_name="blender-mcp")
glama_generate_reports()  # all repos

# Auto-discover repos from Glama
glama_status(operation="discover")
```

## Documentation

| Doc | Contents |
|-----|----------|
| [Installation](INSTALL.md) | All install methods, prerequisites |
| [Configuration](docs/CONFIGURATION.md) | Env vars, fleet-repos.json, LLM setup |
| [Glama Scoring Guide](docs/GLAMA_SCORING.md) | TDQS explained: 6 dimensions, formula, grade thresholds, improvement workflow |
| [Tool Reference](docs/TOOLS.md) | All 7 tools, 2 prompts, 12 operations |
| [Development](docs/DEVELOPMENT.md) | Contributing, local setup, Tauri build |

## Requirements

- MCP client: Claude Desktop, Cursor, or any client supporting MCP tools
- For MCPB: Claude Desktop (drag-and-drop)
- For clone/run: Python 3.11+, uv
- For NSIS installer: Windows 10/11, WebView2 runtime (included in Win11)
- For LLM features: Ollama, LM Studio, or OpenAI API key

## License

MIT
