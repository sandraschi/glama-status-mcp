"""Import smoke test for glama-status-mcp."""
from glama_status_mcp.database import init_db, seed_fleet
from glama_status_mcp.models import FLEET_REPOS

init_db()
seed_fleet(FLEET_REPOS)
print("  Import OK")
