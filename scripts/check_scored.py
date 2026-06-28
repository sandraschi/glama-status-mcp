"""Check which sandraschi repos have score data."""
import asyncio
from glama_status_mcp.scraper import scrape_repo
from glama_status_mcp.models import FLEET_REPOS


async def main():
    results = await asyncio.gather(
        *(scrape_repo(r.name, r.glama_author, r.glama_slug) for r in FLEET_REPOS)
    )
    scored = [(FLEET_REPOS[i].name, r) for i, r in enumerate(results) if r and r.tools]
    unscored = [(FLEET_REPOS[i].name, r) for i, r in enumerate(results) if not r or not r.tools]
    
    print(f"Total: {len(FLEET_REPOS)} repos")
    print(f"Scored: {len(scored)}")
    print(f"Unscored: {len(unscored)}")
    print()
    
    print("=== SCORED ===")
    for name, r in sorted(scored, key=lambda x: x[1].overall_score or 0):
        print(f"  {name}: {r.overall_grade} ({r.overall_score}) - {len(r.tools)} tools")
    
    print()
    print("=== UNSCORED ===")
    for name, r in unscored:
        status = "no page" if not r else "page exists but empty"
        print(f"  {name}: {status}")


asyncio.run(main())
