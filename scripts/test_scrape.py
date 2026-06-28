"""Test scrape all 3 fleet repos and verify output."""
import asyncio
from glama_status_mcp.database import init_db, seed_fleet, upsert_repo_score, create_snapshot, get_all_repo_scores
from glama_status_mcp.models import FLEET_REPOS
from glama_status_mcp.scraper import scrape_repo


async def main():
    init_db()
    seed_fleet(FLEET_REPOS)

    results = await asyncio.gather(*(scrape_repo(r.name) for r in FLEET_REPOS))

    for i, r in enumerate(results):
        if r:
            upsert_repo_score(r)
            print(f"{FLEET_REPOS[i].name}: grade={r.overall_grade} score={r.overall_score} tools={len(r.tools)}")
            print(f"  Coherence: {r.coherence.grade} | TDQS: {r.tdqs_grade} mean={r.tdqs_mean} min={r.tdqs_min} | Maint: {r.maintenance_grade}")
            for t in sorted(r.tools, key=lambda x: x.score):
                print(f"  - {t.name}: {t.grade} {t.score}/5")
        else:
            print(f"{FLEET_REPOS[i].name}: NO SCORE PAGE (404 or error)")

    from glama_status_mcp.database import log_refresh_start, log_refresh_end
    log_id = log_refresh_start()
    log_refresh_end(log_id, len(results), sum(1 for r in results if r), sum(1 for r in results if not r), [])
    snap = create_snapshot(log_id)
    print(f"\nSnapshot: {snap}")

    repos = get_all_repo_scores()
    print(f"\nDB has {len(repos)} repos:")
    for r in repos:
        print(f"  {r['name']}: {r['overall_grade']} ({r['overall_score']}) - {len(r['tools'])} tools")


asyncio.run(main())
