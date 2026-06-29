# Tool Reference

## glama_status (portmanteau, MUTATING)

12 operations for fleet score management.

| Operation | Params | Description |
|-----------|--------|-------------|
| `list` | `limit=50` | All repos worst-first with pagination |
| `get` | `repo_name` (req) | Full per-tool 6-dimension breakdown |
| `worst_tools` | `limit=50` | Lowest-scoring tools fleet-wide |
| `refresh` | -- | Rescrape all fleet repos + create snapshot |
| `history` | `limit=10` | Recent refresh log entries |
| `staleness` | -- | Repos with data older than 7 days |
| `report` | -- | Full structured daily status report |
| `deltas` | -- | Score changes since last snapshot |
| `add_repo` | `repo_name` (req) | Add a repo to the tracking config |
| `remove_repo` | `repo_name` (req) | Remove a repo from tracking |
| `reload_config` | -- | Reload `config/fleet-repos.json` |
| `discover` | -- | Auto-find all repos for the configured author on Glama |

## glama_scores_summary (READ_ONLY)

Compact grade distribution and per-repo stats. No params.

## glama_daily_report (READ_ONLY)

Full markdown report with grade table, score deltas, worst tools, stale repos.

| Param | Default | Description |
|-------|---------|-------------|
| `format` | `"markdown"` | `"markdown"` or `"json"` |

## glama_agentic_analyze (MUTATING, requires sampling-capable client)

Uses MCP `ctx.sample()` to call back to the CONNECTED LLM (Claude
Desktop or Cursor) for autonomous analysis of Glama scores.
Generates a summary, top 5 fixes, and common patterns.

This is the **sampling-based analysis path** -- the LLM runs as part
of the MCP client (not a separate local server). Falls back with
a clear error message when sampling is unavailable.

| Param | Default | Description |
|-------|---------|-------------|
| `repo_name` | `""` | Target repo, or empty for fleet-wide analysis |

## glama_generate_reports (MUTATING)

Writes per-repo markdown reports to `reports/`. When `use_llm=True`
(default) and a local/cloud LLM is reachable, includes AI-powered
per-tool analysis. Falls back to template-based fix todos otherwise.

| Param | Default | Description |
|-------|---------|-------------|
| `repo_name` | `""` | Single repo, or empty for all repos |
| `use_llm` | `True` | Use configured LLM for analysis; falls back to template when unavailable |

Two analysis paths for the price of one:
- **LLM analysis** (default): auto-discovers Ollama/LM Studio/OpenAI, sends tool scores to the LLM, includes AI-generated per-tool fix recommendations in `reports/{repo}.md`
- **Template fallback**: when no LLM is available, generates prioritized fix-todo list based on dimension score thresholds

## show_glama_status_card (Prefab card)

Fleet overview card with grade distribution, per-repo scores, worst tools, stale repos.

## show_glama_repo_card(repo_name) (Prefab card)

Per-repo breakdown card with overall grade, TDQS, coherence, per-tool scores.

## Prompts

| Prompt | Description |
|--------|-------------|
| `glama_improvement_plan(repo_name)` | Per-tool fix priorities with 6 dimension scores |
| `glama_fleet_analysis_prompt()` | Fleet-wide health snapshot for LLM ingestion |
