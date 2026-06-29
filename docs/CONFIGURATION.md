# Configuration

## fleet-repos.json

The tracked fleet is defined in `config/fleet-repos.json`. Each entry:

```json
[
  {"name": "email-mcp", "glama_author": "sandraschi", "glama_slug": "", "active": true}
]
```

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `name` | yes | -- | Repo name (matches Glama slug unless `glama_slug` is set) |
| `glama_author` | no | `sandraschi` | Glama/GitHub author namespace |
| `glama_slug` | no | `""` | Overrides Glama URL slug if it differs from repo name |
| `active` | no | `true` | Set `false` to skip during refresh |

Populate via the `discover` operation or edit the file directly.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GLAMA_AUTHOR` | `sandraschi` | Default author for score URLs and discover |
| `GLAMA_SCRAPE_TIMEOUT` | `30` | HTTP timeout per scrape (seconds) |
| `GLAMA_SCRAPE_DELAY` | `1.0` | Delay between consecutive scrapes (seconds) |
| `GLAMA_USE_BRIGHTDATA` | (unset) | Set to `1` to proxy via BrightData |
| `GLAMA_BRIGHTDATA_TOKEN` | (unset) | BrightData proxy auth token |

## LLM Providers

| Provider | Detection | Requirement |
|----------|-----------|-------------|
| Ollama | Probes `127.0.0.1:11434` | `ollama serve` running |
| LM Studio | Probes `127.0.0.1:1234` | Local API server enabled |
| OpenAI | `OPENAI_API_KEY` env var | `OPENAI_BASE_URL` (optional, defaults to `https://api.openai.com/v1`) |

## Web Dashboard Settings

The Settings page has a "GitHub Account" input. This sets the default author
used for all Glama score and tool page links in the webapp. Stored in
localStorage as `glama-status-gh-account`.
