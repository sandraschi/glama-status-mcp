"""Test scrape fleet repos and verify output."""
import asyncio
from glama_status_mcp.database import init_db, seed_fleet, upsert_repo_score, create_snapshot, log_refresh_start, log_refresh_end, get_all_repo_scores
from glama_status_mcp.models import FLEET_REPOS
from glama_status_mcp.scraper import scrape_repo


async def main():
    init_db()
    seed_fleet(FLEET_REPOS)

    results = []
    for repo in FLEET_REPOS:
        slug = repo.glama_slug or repo.name
        r = await scrape_repo(repo.name, repo.glama_author, slug)
        results.append(r)
        if r and r.tools:
            upsert_repo_score(r)
            print(f"{repo.name} (slug={slug}): grade={r.overall_grade} score={r.overall_score} tools={len(r.tools)}")
        else:
            print(f"{repo.name} (slug={slug}): {'empty (no tools)' if r else 'NO SCORE PAGE'}")

    log_id = log_refresh_start()
    log_refresh_end(log_id, len(results), sum(1 for r in results if r), sum(1 for r in results if not r), [])
    snap = create_snapshot(log_id)
    print(f"\nSnapshot: {snap}")

    repos = get_all_repo_scores()
    print(f"\nDB has {len(repos)} repos with scores:")
    for r in repos:
        print(f"  {r['name']}: {r['overall_grade']} ({r['overall_score']}) - {len(r['tools'])} tools")


asyncio.run(main())
