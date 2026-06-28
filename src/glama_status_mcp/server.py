import asyncio
import json
import sys
from datetime import datetime, timezone
from typing import Optional

from fastmcp import FastMCP, Context

from glama_status_mcp.config import DATA_DIR, GLAMA_AUTHOR, SCRAPE_DELAY
from glama_status_mcp.database import (
    init_db, seed_fleet, upsert_repo_score, get_all_repo_scores,
    get_repo_score, get_worst_tools, log_refresh_start,
    log_refresh_end, get_refresh_history, create_snapshot,
    generate_report, compute_deltas,
)
from glama_status_mcp.models import FLEET_REPOS, RepoScore
from glama_status_mcp.scraper import scrape_repo

mcp = FastMCP("glama-status-mcp", dependencies=["httpx", "beautifulsoup4", "lxml", "aiosqlite"])

_README_ONLY = {"readonly": True}
_MUTATING = {}


@mcp.tool(annotations=_MUTATING)
async def glama_status(
    operation: str,
    repo_name: Optional[str] = None,
    limit: int = 50,
    ctx: Optional[Context] = None,
) -> dict:
    """Fleet-wide Glama score tracker — query per-tool TDQS grades, identify worst-scoring tools, trigger rescans.

    When to use: call this to check the health of any fleet repo's Glama score, find which tools need docstring fixes, or trigger a refresh.
    When NOT to use: for code-level diagnostics use the repo's own tools; for Glama submission/review use glama.ai directly.
    Preconditions: the repo must have been submitted to Glama and scored at least once.

    Operations:
    - list:        Return all repos with current overall grades, ordered worst-first.
    - get:         Return full per-tool breakdown for one repo. Requires repo_name.
    - worst_tools: Return the lowest-scoring tools across the fleet. Use limit to control count.
    - refresh:     Immediately rescrape all fleet repos from Glama and update the database.
    - history:     Return recent refresh log entries.
    - staleness:   Return repos whose Glama data is >7 days old — they need a release + rescan.
    - report:      Return a full daily status report with grade distribution, deltas, worst tools, and stale repos.
    - deltas:      Return score changes between the last two snapshots only.

    Args:
        operation: Action to perform. One of: "list", "get", "worst_tools", "refresh", "history", "staleness".
        repo_name: Required for get. The fleet repo name (e.g. "virtualization-mcp").
        limit: Max results for list, worst_tools, and history. Default 50, max 200.

    Returns:
        Dict with:
          success (bool): True on success.
          operation (str): Echo of the requested operation.
          data (list | dict): Operation-specific payload.
          count (int): Number of items in data (for list/result sets).
          message (str): Human-readable summary.
        On failure: success=False, error (str).
    """
    if operation in ("list",):
        repos = get_all_repo_scores()
        return {
            "success": True,
            "operation": operation,
            "data": repos,
            "count": len(repos),
            "message": f"Found {len(repos)} repos with Glama scores.",
        }

    elif operation == "get":
        if not repo_name:
            return {"success": False, "error": "repo_name required for get operation."}
        repo = get_repo_score(repo_name)
        if not repo:
            return {"success": False, "error": f"Repo '{repo_name}' not found in database. Try refresh first.", "recovery_options": [f"Run glama_status with operation='refresh' to scrape '{repo_name}' from Glama."]}
        return {
            "success": True,
            "operation": operation,
            "data": repo,
            "message": f"Found {len(repo.get('tools', []))} tools for {repo_name}.",
        }

    elif operation == "worst_tools":
        capped = min(limit, 200)
        tools = get_worst_tools(capped)
        return {
            "success": True,
            "operation": operation,
            "data": tools,
            "count": len(tools),
            "message": f"Found {len(tools)} worst-scoring tools across the fleet.",
        }

    elif operation == "refresh":
        return await _do_refresh(ctx)

    elif operation == "history":
        capped = min(limit, 50)
        entries = get_refresh_history(capped)
        return {
            "success": True,
            "operation": operation,
            "data": entries,
            "count": len(entries),
            "message": f"Found {len(entries)} refresh log entries.",
        }

    elif operation == "staleness":
        repos = get_all_repo_scores()
        now = datetime.now(timezone.utc)
        stale = []
        for r in repos:
            if r.get("last_scraped"):
                try:
                    ts = datetime.fromisoformat(r["last_scraped"])
                    days = (now - ts).days
                    if days > 7:
                        stale.append({**r, "days_stale": days})
                except ValueError:
                    stale.append({**r, "days_stale": -1})
        return {
            "success": True,
            "operation": operation,
            "data": stale,
            "count": len(stale),
            "message": f"Found {len(stale)} repos with data older than 7 days.",
        }

    elif operation == "report":
        report = generate_report()
        msg = (
            f"Report: {report['total_repos']} repos, "
            f"{report['grade_distribution'].get('A', 0)}A/{report['grade_distribution'].get('B', 0)}B/"
            f"{report['grade_distribution'].get('C', 0)}C/{report['grade_distribution'].get('D', 0)}D/"
            f"{report['grade_distribution'].get('F', 0)}F, "
            f"{len(report['deltas'])} changes, "
            f"{len(report['stale_repos'])} stale"
        )
        return {
            "success": True,
            "operation": operation,
            "data": report,
            "message": msg,
        }

    elif operation == "deltas":
        deltas = compute_deltas()
        return {
            "success": True,
            "operation": operation,
            "data": deltas,
            "count": len(deltas),
            "message": f"Found {len(deltas)} repos with score changes.",
        }

    return {
        "success": False,
        "error": f"Unknown operation '{operation}'.",
        "recovery_options": ["Use one of: list, get, worst_tools, refresh, history, staleness, report, deltas."],
    }


async def _do_refresh(ctx: Optional[Context] = None) -> dict:
    log_id = log_refresh_start()
    errors: list[str] = []
    succeeded = 0
    failed = 0
    total = len(FLEET_REPOS)

    for i, repo in enumerate(FLEET_REPOS):
        if ctx:
            ctx.info(f"Scraping {repo.name} ({i+1}/{total})...")
        try:
            result = await scrape_repo(repo.name, repo.glama_author)
            if result:
                upsert_repo_score(result)
                succeeded += 1
                if ctx:
                    ctx.info(f"  {repo.name}: grade {result.overall_grade}, {len(result.tools)} tools")
            else:
                failed += 1
                errors.append(f"{repo.name}: no score page found (404)")
        except Exception as e:
            failed += 1
            errors.append(f"{repo.name}: {e}")
        await asyncio.sleep(SCRAPE_DELAY)

    log_refresh_end(log_id, total, succeeded, failed, errors)
    snapshot_id = create_snapshot(log_id) if succeeded > 0 else None

    msg = f"Refreshed {succeeded}/{total} repos. {failed} failed."
    if errors:
        msg += f" Errors: {'; '.join(errors[:5])}"
        if len(errors) > 5:
            msg += f" (+{len(errors)-5} more)"

    return {
        "success": succeeded > 0,
        "operation": "refresh",
        "data": {
            "total": total,
            "succeeded": succeeded,
            "failed": failed,
            "errors": errors[:10],
            "snapshot_id": snapshot_id,
        },
        "message": msg,
    }


@mcp.tool(annotations=_README_ONLY)
async def glama_scores_summary() -> dict:
    """Return a compact fleet-wide score summary — grades per repo and count per grade bucket.

    Args: None.

    Returns:
        Dict with:
          success (bool): Always True.
          grade_distribution (dict): Count of repos per grade (A/B/C/D/F/none).
          repos (list): Each repo with name, grade, overall_score, tdqs_mean, tdqs_min.
          message (str): Summary string.
    """
    repos = get_all_repo_scores()
    grades: dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0, "none": 0}
    summary = []
    for r in repos:
        g = r.get("overall_grade") or "none"
        grades[g] = grades.get(g, 0) + 1
        summary.append({
            "name": r["name"],
            "grade": r.get("overall_grade"),
            "score": r.get("overall_score"),
            "tdqs_mean": r.get("tdqs_mean"),
            "tdqs_min": r.get("tdqs_min"),
            "tools": len(r.get("tools", [])),
            "last_scraped": r.get("last_scraped"),
        })
    return {
        "success": True,
        "grade_distribution": grades,
        "repos": summary,
        "count": len(summary),
        "message": f"{len(summary)} repos: {grades.get('A', 0)}A/{grades.get('B', 0)}B/{grades.get('C', 0)}C/{grades.get('D', 0)}D/{grades.get('F', 0)}F",
    }


@mcp.tool(annotations=_README_ONLY)
async def glama_daily_report(format: str = "markdown") -> dict:
    """Generate a daily fleet health report with grade distribution, recent changes, worst tools, and stale repos.

    When to use: call this once per day (or on demand) to get a comprehensive overview of fleet Glama scores.
    When NOT to use: for individual repo details use glama_status(operation='get').
    Preconditions: at least one refresh must have been run.

    Args:
        format: Output format. "markdown" for human-readable, "json" for raw data. Default "markdown".

    Returns:
        Dict with:
          success (bool): Always True.
          format (str): Echo of requested format.
          markdown (str): Formatted report (for format="markdown").
          data (dict): Raw report data (always included).
          message (str): Summary line.
    """
    report = generate_report()
    deltas = compute_deltas()

    # Build markdown
    grades = report["grade_distribution"]
    lines = [
        "# Glama Fleet Status Report",
        f"Generated: {report['generated_at'][:19]}",
        f"Snapshot: {report['snapshot_time'] or 'N/A'}",
        f"Repos tracked: {report['total_repos']}",
        "",
        "## Grade Distribution",
        f"**A**: {grades.get('A', 0)}  **B**: {grades.get('B', 0)}  **C**: {grades.get('C', 0)}  "
        f"**D**: {grades.get('D', 0)}  **F**: {grades.get('F', 0)}  **unscored**: {grades.get('none', 0)}",
        "",
    ]

    # Delta section
    deltas_with_change = [d for d in deltas if d.get("score_change") is not None and d["score_change"] != 0]
    if deltas_with_change:
        lines.append("## Score Changes Since Last Snapshot")
        lines.append("")
        for d in sorted(deltas_with_change, key=lambda x: abs(x["score_change"]), reverse=True):
            arrow = "▲" if (d["score_change"] or 0) > 0 else "▼"
            lines.append(f"- {d['repo_name']}: {d['previous_score']} → {d['current_score']} ({arrow}{d['score_change']:+.2f})")
        lines.append("")

    # All repos table
    lines.append("## All Repos (worst first)")
    lines.append("")
    lines.append("| Repo | Grade | Score | TDQS μ | TDQS min | Tools | Worst Tool | Stale |")
    lines.append("|------|-------|-------|--------|----------|-------|------------|-------|")
    for r in report["repos"]:
        tools = r.get("tools", [])
        worst = min(tools, key=lambda t: t.get("score", 5)) if tools else None
        worst_name = worst["name"] if worst else "-"
        worst_score = f"{worst['score']:.1f}" if worst else "-"
        stale_flag = ""
        if r.get("last_scraped"):
            try:
                from datetime import datetime, timezone
                days = (datetime.now(timezone.utc) - datetime.fromisoformat(r["last_scraped"])).days
                if days > 7:
                    stale_flag = f"⚠ {days}d"
            except ValueError:
                pass
        lines.append(
            f"| {r['name']} | {r.get('overall_grade') or '-'} | {r.get('overall_score') or '-':>5} | "
            f"{r.get('tdqs_mean') or '-':>5} | {r.get('tdqs_min') or '-':>5} | "
            f"{len(tools)} | {worst_name} ({worst_score}) | {stale_flag} |"
        )
    lines.append("")

    # Worst tools fleet-wide
    wt = report.get("worst_tools_fleet", [])
    if wt:
        lines.append("## Worst Tools Fleet-Wide")
        lines.append("")
        lines.append("| Tool | Repo | Score | Grade |")
        lines.append("|------|------|-------|-------|")
        for t in wt:
            lines.append(f"| {t['tool_name']} | {t['repo_name']} | {t['tool_score']} | {t['tool_grade']} |")
        lines.append("")

    # Stale repos
    stale = report.get("stale_repos", [])
    if stale:
        lines.append("## Stale Repos (>7 days since last scrape)")
        lines.append("")
        lines.append("These repos need a release + Sync Server on glama.ai:")
        for s in stale:
            lines.append(f"- {s['name']} ({s['days']} days stale)")
        lines.append("")

    mk = "\n".join(lines)
    return {
        "success": True,
        "format": format,
        "markdown": mk,
        "data": report,
        "message": f"Report generated: {report['total_repos']} repos, {len(deltas_with_change)} changes, {len(stale)} stale",
    }


@mcp.prompt()
def glama_improvement_plan(repo_name: str) -> str:
    """Generate a docstring improvement plan for a repo based on its Glama scores."""
    repo = get_repo_score(repo_name)
    if not repo:
        return f"Repo '{repo_name}' not found in the database. Run a refresh first."
    lines = [
        f"# Glama improvement plan: {repo_name}",
        f"Current grade: {repo.get('overall_grade', '?')} (score: {repo.get('overall_score', '?')})",
        f"TDQS mean: {repo.get('tdqs_mean', '?')} | TDQS min: {repo.get('tdqs_min', '?')}",
        "",
        "## Per-tool priorities (worst first)",
    ]
    for t in sorted(repo.get("tools", []), key=lambda x: x.get("score", 5)):
        dims = [
            f"Purpose={t.get('purpose', '?')}",
            f"Usage={t.get('usage_guidelines', '?')}",
            f"Behavior={t.get('behavior', '?')}",
            f"Params={t.get('parameters', '?')}",
            f"Conciseness={t.get('conciseness', '?')}",
            f"Completeness={t.get('completeness', '?')}",
        ]
        lines.append(f"- **{t.get('name')}** ({t.get('grade', '?')}, {t.get('score', '?')}/5) — {' | '.join(dims)}")
    lines.extend([
        "",
        "### Fix plan",
        "1. Fix the worst tool first (it pulls the whole server down via the 60/40 mean/min formula)",
        "2. Add missing parameter descriptions via `Field(description=...)`",
        "3. Add behavioral warnings for destructive operations",
        "4. Add 'When to use' / 'When NOT to use' guidance",
        "5. Keep docstrings 80-250 words",
        "6. Make a release, push to PyPI, then trigger 'Sync Server' on glama.ai",
    ])
    return "\n".join(lines)


def _init():
    init_db()
    seed_fleet(FLEET_REPOS)


def main():
    _init()
    if "--http" in sys.argv:
        import uvicorn
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.staticfiles import StaticFiles
        from pathlib import Path

        app = FastAPI(title="glama-status-mcp")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

        asgi_app = mcp.http_app()

        @app.get("/health")
        async def health():
            return {"status": "ok", "service": "glama-status-mcp"}

        @app.get("/api/repos")
        async def api_repos():
            return get_all_repo_scores()

        @app.get("/api/repos/{name}")
        async def api_repo(name: str):
            repo = get_repo_score(name)
            if not repo:
                return {"error": "not found"}, 404
            return repo

        @app.get("/api/worst-tools")
        async def api_worst_tools(limit: int = 20):
            return get_worst_tools(limit)

        @app.post("/api/refresh")
        async def api_refresh():
            result = await _do_refresh()
            return result

        @app.get("/api/history")
        async def api_history(limit: int = 10):
            return get_refresh_history(limit)

        @app.get("/api/report")
        async def api_report():
            return generate_report()

        @app.get("/api/deltas")
        async def api_deltas():
            return compute_deltas()

        webapp_dir = Path(__file__).resolve().parent.parent.parent / "webapp" / "dist"
        if webapp_dir.exists():
            app.mount("/", StaticFiles(directory=str(webapp_dir), html=True), name="webapp")

        port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 11072
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
