# Changelog

## v0.1.1 (2026-06-29)

Beta release -- fleet standard webapp, LLM chat, agentic analysis, Tauri NSIS.

### Fixed
- MCP HTTP transport properly mounted at `/mcp` on FastAPI app
- 57 ruff lint errors resolved (imports, line length, type annotations, unused vars)
- Grade regex hardened for lxml whitespace quirks
- `start.ps1` ErrorAction/Out-Null pipeline fix for uv stderr
- FastMCP `dependencies` kwarg removed (not supported in 3.4+)
- Glama tool URLs corrected to `glama.ai/tools/{name}` (not `/mcp/tools/`)
- TypeScript type conflicts resolved (shared `types.ts`)

### Added
- **LLM integration**: Glom-On auto-discovery (Ollama 11434, LM Studio 1234, OpenAI)
- **Chat page**: 4 personalities, provider/model selector, conversation history, export/clear
- **Agentic MCP tool**: `glama_agentic_analyze` using `ctx.sample()` for LLM-powered score analysis
- **Report generation**: `glama_generate_reports` writes per-repo markdown to `reports/`
- **MCP prompt**: `glama_fleet_analysis_prompt` for fleet-wide LLM health analysis
- **Prefab UI cards**: `show_glama_status_card` (fleet overview), `show_glama_repo_card` (per-repo)
- **Configurable fleet**: `config/fleet-repos.json` for tracking any Glama author's repos
- **Operations**: `add_repo`, `remove_repo`, `reload_config` in `glama_status` tool
- **6-page webapp**: Dashboard, Report, Tools, Chat, Help, Settings
- **Retractable sidebar**: collapse toggle, grade summary bar, integrated refresh
- **Glama links**: every repo row and tool name links to glama.ai score/tool pages
- **Hero section**: 3-column fleet health summary on Dashboard
- **Tauri 2.0 NSIS installer**: 32.6 MB, embedded PyInstaller backend, single shortcut
- **MCPB bundle**: 131 KB drag-and-drop for Claude Desktop
- 35 backend tests (database, scraper, server API)
- Playwright E2E test suite (`webapp/e2e/fleet-audit.spec.ts`)
- Biome TypeScript linting config
- `scripts/refresh.py` for scheduled rescrapes
- `scripts/smoke.py` import verification

### Changed
- Webapp: TailwindCSS v4, Lucide React, Zustand, Framer Motion
- `bg-gray-950` -> `bg-zinc-950` (fleet Zinc palette)
- All font contrast bumped (zinc-600->500, zinc-500->400)
- Generic messaging: "your MCP fleet" (not sandraschi-specific)
- Sidebar layout with persistent nav across all pages
- README badges: FastMCP 3.4.2, 35 passed, ruff, TS strict, MIT, Tauri

### Removed
- 15 debug inspect scripts from `scripts/`
- `package-lock.json` (switched to Bun)

## v0.1.0 (2026-06-28)

Initial release.
