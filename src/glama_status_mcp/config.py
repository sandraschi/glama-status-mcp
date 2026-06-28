import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "glama_status.db"
GLAMA_BASE = "https://glama.ai/mcp/servers"
GLAMA_AUTHOR = os.getenv("GLAMA_AUTHOR", "sandraschi")
SCRAPE_TIMEOUT = int(os.getenv("GLAMA_SCRAPE_TIMEOUT", "30"))
SCRAPE_DELAY = float(os.getenv("GLAMA_SCRAPE_DELAY", "1.0"))
