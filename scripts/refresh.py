"""Refresh all fleet repo Glama scores and create a snapshot.

Usage: uv run python scripts/refresh.py
"""
import asyncio

from glama_status_mcp.database import (
    init_db, seed_fleet, upsert_repo_score,
    create_snapshot, log_refresh_start, log_refresh_end,
)
from glama_status_mcp.models import FLEET_REPOS
from glama_status_mcp.scraper import scrape_repo


async def main():
    init_db()
    seed_fleet(FLEET_REPOS)
    log_id = log_refresh_start()
    total = len(FLEET_REPOS)
    print(f"Scraping {total} repos...")

    succeeded = 0
    failed = 0
    errors: list[str] = []

    for repo in FLEET_REPOS:
        try:
            result = await scrape_repo(
                repo.name, repo.glama_author, repo.glama_slug
            )
            if result and result.tools:
                upsert_repo_score(result)
                succeeded += 1
                print(f"  {repo.name}: grade {result.overall_grade}, "
                      f"{len(result.tools)} tools")
            elif result and not result.tools:
                errors.append(
                    f"{repo.name}: page exists, no tools scored"
                )
            else:
                errors.append(f"{repo.name}: no score page found (404)")
        except Exception as e:
            failed += 1
            errors.append(f"{repo.name}: {e}")

    log_refresh_end(log_id, total, succeeded, failed, errors[:10])
    snapshot_id = create_snapshot(log_id) if succeeded > 0 else None
    print(f"Done: {succeeded}/{total}, snapshot={snapshot_id}")
    if errors:
        print("Errors:")
        for e in errors[:5]:
            print(f"  - {e}")


if __name__ == "__main__":
    asyncio.run(main())
