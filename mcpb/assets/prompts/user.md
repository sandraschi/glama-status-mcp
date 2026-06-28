# glama-status-mcp User Guide

Welcome to glama-status-mcp, your fleet's Glama score dashboard. This guide walks you through setup, daily workflows, and advanced features.

## Getting Started

### 1. Install

```bash
git clone https://github.com/sandraschi/glama-status-mcp.git
cd glama-status-mcp
just install
.\start.ps1          # backend + frontend + browser at :11073
```

The server starts on port 11072 (FastAPI + MCP HTTP at /mcp) and the web dashboard opens at port 11073.

### 2. Register in Claude Desktop

If you want to use the MCP tools directly from Claude Desktop or Cursor:

```json
{
  "mcpServers": {
    "glama-status": {
      "command": "uv",
      "args": [
        "--directory", "C:\\path\\to\\glama-status-mcp",
        "run", "glama-status-mcp"
      ],
      "env": { "PYTHONUNBUFFERED": "1" }
    }
  }
}
```

### 3. First Refresh

Before the dashboard shows any data, you need to scrape Glama:

```python
# Via MCP tool
glama_status(operation="refresh")

# Or CLI
just refresh
```

This scrapes all repos in `config/fleet-repos.json` and populates the database. The default config ships with 10 example repos. Edit it to track your own.

### 4. Open the Dashboard

Browse to `http://127.0.0.1:11073`. You'll see the 6-page web interface:
- **Dashboard**: Hero section with fleet health summary + sortable repo table
- **Report**: Grade distribution, score deltas, worst tools, stale repos
- **Tools**: All tools grouped by grade, each linked to Glama
- **Chat**: LLM-powered analysis with auto-discovered providers
- **Help**: Documentation with 5 tabs
- **Settings**: Configure your GitHub/Glama account name

## Daily Workflow

### Morning Check (30 seconds)

```
1. Open http://127.0.0.1:11073
2. Check the hero section: grade spread, weakest link, worst tool
3. Click "Report" in the sidebar -- see score changes since yesterday
4. Click "Tools" -- scan for any new F-grade tools
5. If any repos are stale (>7 days), push a release and trigger Sync Server on glama.ai
```

### Deep Dive on a Repo (5 minutes)

```
1. Dashboard: click any repo row to drill into per-tool breakdown
2. See all tools sorted worst-first with 6 dimension bars
3. Click any tool name (blue link) to open its Glama detail page
4. Click the external-link icon next to the repo name to open the Glama score page
```

### LLM-Powered Analysis

The Chat page lets you ask an LLM about your scores:

```
1. Start Ollama (ollama serve) or LM Studio locally
2. Open the Chat page in the web dashboard
3. The provider and model should be auto-detected
4. Select a personality: "Glama Analyst" is recommended for score analysis
5. Try prompts like:
   - "Analyze blender-mcp scores and give me 3 fixes"
   - "What common docstring problems do you see?"
   - "Compare email-mcp and steam-mcp tool quality"
   - "Which repo needs the most urgent attention?"
```

### Agentic Analysis via MCP

If your MCP client supports sampling (Claude Desktop, Cursor):

```python
# LLM will analyze all tools and produce specific, actionable fixes
glama_agentic_analyze(repo_name="blender-mcp")

# Fleet-wide analysis
glama_agentic_analyze()
```

The LLM receives every tool's scores, 6 dimension breakdowns, and the TDQS formula. It produces:
1. A one-paragraph summary of the state
2. The 5 most impactful fixes (specific, actionable)
3. Patterns it notices across tools (e.g., "all missing parameter descriptions")

### Generate Fix Reports

Write per-repo markdown reports for your IDE LLM:

```python
# One repo
glama_generate_reports(repo_name="email-mcp")
# -> writes reports/email-mcp.md

# All repos
glama_generate_reports()
# -> writes reports/*.md + reports/fleet-report.md
```

These reports include tool-by-tool breakdowns with dimension scores, prioritized fix todos, and a quick reference checklist. Feed them to your IDE's LLM agent for automated fixes.

## Tracking Your Own Repos

### Via MCP Tool

```python
# Add a repo from any Glama author
glama_status(operation="add_repo", repo_name="my-cool-mcp")

# Add with explicit author
glama_status(operation="add_repo", repo_name="their-mcp", author="other-user")

# Scrape immediately
glama_status(operation="refresh")
```

### Via Config File

Edit `config/fleet-repos.json`:

```json
[
  {"name": "my-cool-mcp", "glama_author": "my-github-name"},
  {"name": "their-mcp", "glama_author": "other-user", "glama_slug": "their-mcp-server"},
  {"name": "another-one", "glama_author": "my-github-name", "active": true}
]
```

Then reload:

```python
glama_status(operation="reload_config")
```

The `glama_slug` field is for repos where the Glama URL slug differs from the repo name (e.g., the GitHub repo is "their-mcp" but Glama lists it as "their-mcp-server").

### Via Web Dashboard Settings

The Settings page has a "GitHub Account" input. Change it to your GitHub username, and new repos added via `add_repo` will use that as the default Glama author.

## Understanding the Dashboard

### Hero Section (Dashboard)
Three key metrics at a glance:
- **Grade Spread**: Color-coded A/B/C/D/F counts across all tracked repos
- **Weakest Link**: The repo with the lowest overall score -- fix this first
- **Worst Tool**: The single lowest-scoring tool across the entire fleet

### Score Table
- Sortable by score, name, grade, tool count, staleness
- Filter by repo name or grade letter
- Click any row to drill into per-tool breakdown
- External-link icon opens the Glama score page in a new tab

### Tool Breakdown
- All tools sorted worst-first
- 6 dimension bars per tool (Purpose, Usage, Behavior, Params, Conciseness, Completeness)
- Color-coded: green (>=4), blue (>=3), amber (>=2), red (<2)
- "Needs work" badge on tools scoring below 3.0
- Each tool name is a clickable link to glama.ai/tools/{name}
- Improvement hint card at the bottom for repos scoring below 3.5

### Report Page
- Grade distribution with proportional bars
- Score changes since last snapshot (with trend arrows)
- Worst tools fleet-wide list
- Stale repos flagged with day counts

### Tools Page
- All tools across all repos, grouped by grade
- Each tool linked to its Glama detail page
- Grade distribution summary with percentage bars

## Scoring Reference

### The TDQS Formula

Each tool is scored across 6 dimensions on a 0-5 scale. The server-level score is:

```
overall = 0.6 * mean(all_tool_scores) + 0.4 * min(all_tool_scores)
```

This means ONE low-scoring tool pulls the entire server down significantly. The minimum-scoring tool is ALWAYS the highest-leverage fix target.

### 6 Dimensions Explained

**Purpose Clarity (25%)**: The first sentence of the docstring should state exactly what the tool does. Bad: "Handles files." Good: "Creates, reads, and deletes files in the project's output directory."

**Usage Guidelines (20%)**: Clear "When to use" / "When NOT to use" sections. Preconditions documented. Bad: No usage guidance at all. Good: "Use this when you need to batch-process files. Do NOT use for single-file operations -- use file_op instead."

**Behavioral Transparency (20%)**: Return values, side effects, and error conditions are documented. Bad: No mention of what the tool returns. Good: includes "## Return Format" section and lists error conditions.

**Parameter Semantics (15%)**: Every parameter has a type annotation, description, and notes on valid values. Bad: `name: str -- the name`. Good: `name: Annotated[str, Field(description="Project name. Must be 3-50 chars, lowercase, no spaces.")]`.

**Conciseness & Structure (10%)**: Not a wall of text, not a one-liner. Goldilocks zone: 80-250 words. Uses sections (## Return Format, ## Examples).

**Contextual Completeness (10%)**: Can an LLM use this tool correctly without reading the source code? Includes examples, edge cases, and any non-obvious behavior.

### Grade Thresholds

| Grade | Score Range | Meaning |
|-------|-------------|---------|
| A | >= 3.5 | Excellent documentation |
| B | 3.0 - 3.49 | Good, minor improvements |
| C | 2.0 - 2.99 | Adequate, several tools need work |
| D | 1.0 - 1.99 | Poor, major attention needed |
| F | < 1.0 | Failing, urgent overhaul required |

## Fixing Low Scores

### Priority Order
1. Fix the WORST tool first (it has the most leverage on the server score)
2. Add parameter descriptions: `Field(description="...")` on every param
3. Add behavioral warnings: annotate with `READ_ONLY`/`MUTATING`/`DESTRUCTIVE`
4. Add "When to use" / "When NOT to use" sections
5. Keep docstrings in the 80-250 word range
6. Add `## Return Format` and `## Examples` sections

### After Fixing
1. Make a release and push to PyPI
2. Go to glama.ai/mcp/servers and trigger "Sync Server"
3. Wait for Glama to re-score (typically within hours)
4. Run `glama_status(operation="refresh")` to pull the new scores
5. Check the deltas to confirm improvement

## Advanced: LLM Chat Features

The Chat page supports:
- **4 personalities**: Glama Analyst (score-focused), SRE Engineer (risk-focused), Friendly Guide (educational), Short & Punchy (concise)
- **Conversation history**: persisted in localStorage, survives page reloads
- **Export**: download chat as .txt file
- **Clear**: reset to fresh state
- **Example prompts**: click to pre-fill the input
- **Keyboard**: Enter to send, Shift+Enter for newline

### Chat API

The backend exposes `POST /api/chat`:

```json
{
  "message": "Analyze email-mcp scores",
  "model": "llama3.2:3b",
  "base_url": "http://127.0.0.1:11434/v1",
  "provider": "ollama",
  "system_prompt": "You are a Glama TDQS analyst...",
  "context": {
    "history": [
      {"role": "user", "content": "..."},
      {"role": "assistant", "content": "..."}
    ]
  }
}
```

The system prompt is injected from the selected personality. Full conversation history is sent on every request for multi-turn context.

## Scheduled Refresh

Register a Windows Scheduled Task for daily 6:00 AM refresh:

```powershell
just schedule-daily
```

Or via the included PowerShell script:

```powershell
.\scripts\register-daily-refresh.ps1
```

## Native Desktop App (Tauri)

A Tauri 2.0 NSIS installer is available for Windows:

1. Download `Glama Status_0.1.1_x64-setup.exe` from GitHub Releases
2. Run the installer (no admin required, installs per-user)
3. Launch "Glama Status" from the Start Menu or desktop shortcut
4. The embedded Python backend starts automatically, no Python required

The installer is ~32 MB and bundles the PyInstaller-frozen backend + React frontend in a WebView2 shell.

## Troubleshooting

### "No scores yet" on dashboard
Run `just refresh` or click the Refresh button in the sidebar. The database starts empty and needs to be populated.

### "No provider detected" on Chat page
Ensure Ollama or LM Studio is running locally. For Ollama: `ollama serve`. For LM Studio: start the server and enable the local API.

### "ModuleNotFoundError: glama_status_mcp"
Run `uv sync --extra dev --extra web` from the repo root.

### Port already in use
The start script clears ports 11072 and 11073 on launch. If another process is using them, kill it manually or change ports in `start.ps1`.

### Scraper returns empty tools for a repo
The repo exists on Glama but hasn't been analyzed yet. It needs to be submitted for scoring via glama.ai first. Not all registered repos have scores.

### Config changes not taking effect
Call `glama_status(operation="reload_config")` or restart the server.

## FAQ

**Q: Can I track repos from any GitHub account?**
Yes. Edit `config/fleet-repos.json` or use `glama_status(add_repo, repo_name="...", author="...")`.

**Q: How often should I refresh?**
Daily is recommended. The Windows Scheduled Task handles this. Manual refresh is fine for spot-checks.

**Q: Does it work without an LLM?**
Yes. All features work without an LLM. The Chat page and `glama_agentic_analyze` are LLM-optional extras.

**Q: Can I use OpenAI instead of a local LLM?**
Yes. Set `OPENAI_API_KEY` and optionally `OPENAI_BASE_URL` environment variables.

**Q: How do I add repos in bulk?**
Edit `config/fleet-repos.json` with all your repos, then restart or call `reload_config`.

**Q: Why does one low tool pull the whole score down?**
The Glama TDQS formula weights the minimum at 40%. This is by design -- Glama penalizes inconsistent documentation quality across tools.

**Q: What's the difference between the web dashboard and the MCP tools?**
The dashboard is human-facing (browser). The MCP tools are for LLM agents (Claude Desktop, Cursor). The `.mcpb` bundle enables drag-and-drop Claude Desktop installation.
