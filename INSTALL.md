# Install

## Prerequisites

- Windows 10/11
- [winget](https://learn.microsoft.com/en-us/windows/package-manager/winget/) (built-in on Windows 10 1809+)

`start.ps1` will auto-install uv, Node.js, and all Python/frontend dependencies via winget.

## Quickstart

```powershell
.\start.ps1
```

Opens browser at http://127.0.0.1:11073.

## Manual

```powershell
# Install deps
uv sync --extra dev --extra web

# Run backend
uv run python -m glama_status_mcp --http --port 11072

# Run frontend (separate terminal)
cd webapp
npm install
npx vite --port 11073 --host
```

## Ports

- Backend: 11072
- Frontend: 11073
