# Development

## Setup

```bash
git clone https://github.com/sandraschi/glama-status-mcp.git
cd glama-status-mcp
uv sync --extra dev --extra web
```

## Lint & Format

```bash
uv run ruff check src/
uv run ruff format src/ --check
```

## Tests

```bash
uv run pytest tests/ -v
```

## Frontend

```bash
cd webapp
npm install
npm run dev          # Vite dev server on :11073
npm run build        # Production build to dist/
npx tsc --noEmit     # TypeScript check
npx biome check src/ # Biome lint
```

## Tauri Native Build

Requires Rust toolchain (`rustup`), MSVC build tools, and PyInstaller.

```bash
cd native
.\build.ps1          # Full pipeline: frontend → PyInstaller → Tauri NSIS
```

Or step by step:

```bash
# 1. Build frontend
cd webapp && npm run build && cd ..

# 2. PyInstaller backend
uv run .venv\Scripts\pyinstaller.exe glama-status-mcp-backend.spec --clean --noconfirm

# 3. Copy backend to resources
Copy-Item dist\glama-status-mcp-backend.exe native\resources\

# 4. Build Tauri NSIS
cd native && npx @tauri-apps/cli build --bundles nsis
```

## MCPB Bundle

```bash
npx @anthropic-ai/mcpb pack . dist/glama-status-mcp-v0.1.1.mcpb
```

## Database

SQLite at `data/glama_status.db` (6 tables). Schema auto-created on first run.

To reset: delete the database file and restart.
