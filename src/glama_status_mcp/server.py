import asyncio
import sys
from datetime import UTC, datetime

from fastmcp import Context, FastMCP
from fastmcp.server.server import ToolResult
from prefab_ui import PrefabApp
from prefab_ui.components import Badge, Heading, Row

from glama_status_mcp.config import SCRAPE_DELAY
from glama_status_mcp.database import (
    compute_deltas,
    create_snapshot,
    generate_report,
    get_all_repo_scores,
    get_refresh_history,
    get_repo_score,
    get_worst_tools,
    init_db,
    log_refresh_end,
    log_refresh_start,
    seed_fleet,
    upsert_repo_score,
)
from glama_status_mcp.scraper import scrape_repo

mcp = FastMCP("glama-status-mcp")

_READ_ONLY = {"readonly": True}
_MUTATING: dict[str, bool] = {}

_OP_LIST = ("list, get, worst_tools, refresh, history, staleness, "
             "report, deltas, add_repo, remove_repo, reload_config")


@mcp.tool(annotations=_MUTATING)
async def glama_status(
    operation: str,
    repo_name: str | None = None,
    limit: int = 50,
    ctx: Context | None = None,
) -> dict:
    """Fleet-wide Glama score tracker -- query per-tool TDQS grades.

    Identifies worst-scoring tools, trigger rescans.
    When to use: check fleet repo Glama scores, find tools needing
    docstring fixes, or trigger a refresh.
    When NOT to use: for code diagnostics use the repo's own tools;
    for Glama submission/review use glama.ai directly.
    Preconditions: repo must have been submitted to Glama and scored.

    Operations:
    - list:  All repos, worst-first.
    - get:  Per-tool breakdown for one repo (repo_name required).
    - worst_tools:  Lowest-scoring tools fleet-wide.
    - refresh:  Rescrape all fleet repos + snapshot.
    - history:  Recent refresh log entries.
    - staleness:  Repos >7d since last scrape.
    - report:  Full daily status report.
    - deltas:  Score changes between last two snapshots.
    - add_repo:  Add a repo to track (name, optional author/slug).
    - remove_repo:  Stop tracking a repo.
    - reload_config:  Reload fleet-repos.json config file.

    Args:
        operation: One of: list, get, worst_tools, refresh, history,
                   staleness, report, deltas.
        repo_name: Required for get. e.g. "virtualization-mcp".
        limit: Max results. Default 50, max 200.

    Returns:
        success (bool), operation (str),
        data (list|dict), count (int), message (str).
        On failure: success=False, error (str).
    """
    if operation == "list":
        repos = get_all_repo_scores()
        return {
            "success": True,
            "operation": operation,
            "data": repos,
            "count": len(repos),
            "message": f"Found {len(repos)} repos with Glama scores.",
        }

    if operation == "get":
        if not repo_name:
            return {"success": False, "error": "repo_name required."}
        repo = get_repo_score(repo_name)
        if not repo:
            hint = f"Run glama_status(operation='refresh') to scrape '{repo_name}'."
            return {
                "success": False,
                "error": f"Repo '{repo_name}' not found. Try refresh first.",
                "recovery_options": [hint],
            }
        return {
            "success": True,
            "operation": operation,
            "data": repo,
            "message": f"Found {len(repo.get('tools', []))} tools for {repo_name}.",
        }

    if operation == "worst_tools":
        capped = min(limit, 200)
        tools = get_worst_tools(capped)
        return {
            "success": True,
            "operation": operation,
            "data": tools,
            "count": len(tools),
            "message": f"Found {len(tools)} worst-scoring tools fleet-wide.",
        }

    if operation == "refresh":
        return await _do_refresh(ctx)

    if operation == "history":
        capped = min(limit, 50)
        entries = get_refresh_history(capped)
        return {
            "success": True,
            "operation": operation,
            "data": entries,
            "count": len(entries),
            "message": f"Found {len(entries)} refresh log entries.",
        }

    if operation == "staleness":
        repos = get_all_repo_scores()
        now = datetime.now(UTC)
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
            "message": f"Found {len(stale)} repos stale >7 days.",
        }

    if operation == "report":
        report = generate_report()
        gd = report["grade_distribution"]
        msg = (
            f"Report: {report['total_repos']} repos, "
            f"{gd.get('A',0)}A/{gd.get('B',0)}B/"
            f"{gd.get('C',0)}C/{gd.get('D',0)}D/"
            f"{gd.get('F',0)}F, "
            f"{len(report['deltas'])} changes, "
            f"{len(report['stale_repos'])} stale"
        )
        return {
            "success": True,
            "operation": operation,
            "data": report,
            "message": msg,
        }

    if operation == "deltas":
        deltas = compute_deltas()
        return {
            "success": True,
            "operation": operation,
            "data": deltas,
            "count": len(deltas),
            "message": f"Found {len(deltas)} repos with score changes.",
        }

    if operation == "add_repo":
        if not repo_name:
            return {"success": False, "error": "repo_name required."}
        from glama_status_mcp.models import DEFAULT_AUTHOR
        from glama_status_mcp.models import add_repo as _add
        author = DEFAULT_AUTHOR
        new = _add(name=repo_name, author=author)
        return {
            "success": True,
            "operation": operation,
            "data": {"name": new.name, "glama_author": new.glama_author},
            "message": f"Added {repo_name} (author: {new.glama_author}). "
                       f"Run refresh to scrape scores.",
        }

    if operation == "remove_repo":
        if not repo_name:
            return {"success": False, "error": "repo_name required."}
        from glama_status_mcp.models import remove_repo as _remove
        removed = _remove(repo_name)
        return {
            "success": removed,
            "operation": operation,
            "message": f"Removed {repo_name}." if removed
            else f"Repo '{repo_name}' not in fleet.",
        }

    if operation == "reload_config":
        import importlib

        import glama_status_mcp.models as mmod
        importlib.reload(mmod)
        _FR = mmod.load_fleet_repos()
        return {
            "success": True,
            "operation": operation,
            "data": {"count": len(_FR)},
            "message": f"Reloaded config: {len(_FR)} repos tracked.",
        }

    return {
        "success": False,
        "error": f"Unknown operation '{operation}'.",
        "recovery_options": [f"Use one of: {_OP_LIST}."],
    }


async def _do_refresh(ctx: Context | None = None) -> dict:
    from glama_status_mcp.models import FLEET_REPOS as _FR
    log_id = log_refresh_start()
    errors: list[str] = []
    succeeded = 0
    failed = 0
    total = len(_FR)

    for i, repo in enumerate(_FR):
        if ctx:
            ctx.info(f"Scraping {repo.name} ({i + 1}/{total})...")
        try:
            result = await scrape_repo(
                repo.name, repo.glama_author, repo.glama_slug
            )
            if result and result.tools:
                upsert_repo_score(result)
                succeeded += 1
                if ctx:
                    n = len(result.tools)
                    ctx.info(f"  {repo.name}: grade {result.overall_grade}, {n} tools")
            elif result and not result.tools:
                errors.append(
                    f"{repo.name}: page exists, no tools scored (not analyzed)"
                )
            else:
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
            msg += f" (+{len(errors) - 5} more)"

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


@mcp.tool(annotations=_READ_ONLY)
async def glama_scores_summary() -> dict:
    """Return compact fleet-wide score summary.

    Grades per repo and count per grade bucket.
    Returns: success, grade_distribution, repos, count, message.
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
    a = grades.get("A", 0)
    b = grades.get("B", 0)
    c = grades.get("C", 0)
    d = grades.get("D", 0)
    f_g = grades.get("F", 0)
    return {
        "success": True,
        "grade_distribution": grades,
        "repos": summary,
        "count": len(summary),
        "message": f"{len(summary)} repos: {a}A/{b}B/{c}C/{d}D/{f_g}F",
    }


@mcp.tool(annotations=_READ_ONLY)
async def glama_daily_report(format: str = "markdown") -> dict:
    """Generate daily fleet health report.

    Includes grade distribution, recent changes, worst tools, stale repos.
    When to use: once daily for comprehensive fleet Glama score overview.
    When NOT to use: for single repo details use glama_status(get).
    Preconditions: at least one refresh must have been run.

    Args:
        format: "markdown" or "json". Default "markdown".

    Returns:
        success, format, markdown (if markdown), data, message.
    """
    report = generate_report()
    deltas = compute_deltas()

    grades = report["grade_distribution"]
    lines = [
        "# Glama Fleet Status Report",
        f"Generated: {report['generated_at'][:19]}",
        f"Snapshot: {report['snapshot_time'] or 'N/A'}",
        f"Repos tracked: {report['total_repos']}",
        "",
        "## Grade Distribution",
        (
            f"**A**: {grades.get('A', 0)}  **B**: {grades.get('B', 0)}  "
            f"**C**: {grades.get('C', 0)}  **D**: {grades.get('D', 0)}  "
            f"**F**: {grades.get('F', 0)}  "
            f"**unscored**: {grades.get('none', 0)}"
        ),
        "",
    ]

    deltas_with_change = [
        d for d in deltas
        if d.get("score_change") is not None and d["score_change"] != 0
    ]
    if deltas_with_change:
        lines.append("## Score Changes Since Last Snapshot")
        lines.append("")
        key_fn = lambda x: abs(x["score_change"])  # noqa: E731
        for d in sorted(deltas_with_change, key=key_fn, reverse=True):
            arrow = "\u25b2" if (d["score_change"] or 0) > 0 else "\u25bc"
            p = d["previous_score"]
            c = d["current_score"]
            ch = d["score_change"]
            lines.append(f"- {d['repo_name']}: {p} \u2192 {c} ({arrow}{ch:+.2f})")
        lines.append("")

    lines.append("## All Repos (worst first)")
    lines.append("")
    lines.append(
        "| Repo | Grade | Score | TDQS μ | TDQS min | "
        "Tools | Worst Tool | Stale |"
    )
    lines.append(
        "|------|-------|-------|--------|----------|"
        "-------|------------|-------|"
    )
    for r in report["repos"]:
        tools = r.get("tools", [])
        worst = min(tools, key=lambda t: t.get("score", 5)) if tools else None
        wname = worst["name"] if worst else "-"
        wscore = f"{worst['score']:.1f}" if worst else "-"
        stale_flag = ""
        if r.get("last_scraped"):
            try:
                ts = datetime.fromisoformat(r["last_scraped"])
                days = (datetime.now(UTC) - ts).days
                if days > 7:
                    stale_flag = f"\u26a0 {days}d"
            except ValueError:
                pass
        grade = r.get("overall_grade") or "-"
        oscore = r.get("overall_score")
        oscore_str = f"{oscore:>5}" if oscore is not None else "-"
        tmean = r.get("tdqs_mean")
        tmean_str = f"{tmean:>5}" if tmean is not None else "-"
        tmin = r.get("tdqs_min")
        tmin_str = f"{tmin:>5}" if tmin is not None else "-"
        lines.append(
            f"| {r['name']} | {grade} | {oscore_str} | "
            f"{tmean_str} | {tmin_str} | "
            f"{len(tools)} | {wname} ({wscore}) | {stale_flag} |"
        )
    lines.append("")

    wt = report.get("worst_tools_fleet", [])
    if wt:
        lines.append("## Worst Tools Fleet-Wide")
        lines.append("")
        lines.append("| Tool | Repo | Score | Grade |")
        lines.append("|------|------|-------|-------|")
        for t in wt:
            lines.append(
                f"| {t['tool_name']} | {t['repo_name']} | "
                f"{t['tool_score']} | {t['tool_grade']} |"
            )
        lines.append("")

    stale = report.get("stale_repos", [])
    if stale:
        lines.append("## Stale Repos (>7 days)")
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
        "message": (
            f"Report: {report['total_repos']} repos, "
            f"{len(deltas_with_change)} changes, {len(stale)} stale"
        ),
    }


@mcp.tool(app=True)
async def show_glama_status_card() -> ToolResult:
    """Show fleet Glama score overview as a rich Prefab card.

    Displays grade distribution, per-repo scores (worst first), worst
    tools across the fleet, and stale repos in a structured dashboard
    card suitable for in-chat viewing.

    ## Return Format
    ToolResult with PrefabApp card and plain-text fallback.

    ## Examples
    await show_glama_status_card()
    """
    report = generate_report()
    repos = report["repos"]
    grades = report["grade_distribution"]
    worst_tools = report["worst_tools_fleet"]
    stale_repos = report["stale_repos"]

    def _grade_variant(grade: str | None) -> str:
        match grade:
            case "A":
                return "success"
            case "B":
                return "info"
            case "C" | "D":
                return "warning"
            case "F":
                return "error"
            case _:
                return "default"

    with PrefabApp(title="Glama Fleet Status") as app:
        Heading("Grade Distribution")
        for g in ("A", "B", "C", "D", "F"):
            Row(
                label=f"Grade {g}",
                value=str(grades.get(g, 0)),
                badge=Badge(str(grades.get(g, 0)), variant=_grade_variant(g))
                if grades.get(g, 0) else None,
            )

        Heading(f"Repos ({len(repos)}) — Worst First")
        for r in repos[:15]:
            grade = r.get("overall_grade") or "?"
            score = r.get("overall_score")
            score_str = f"{score:.2f}" if score is not None else "?"
            Row(
                label=r["name"],
                value=f"{score_str} ({grade})",
            )

        if worst_tools:
            Heading("Worst Tools Fleet-Wide")
            for t in worst_tools[:5]:
                Row(
                    label=f"{t['tool_name']} ({t['repo_name']})",
                    value=f"{t['tool_score']}/5 [{t['tool_grade']}]",
                )

        if stale_repos:
            Heading("Stale Repos (>7d)")
            for s in stale_repos[:5]:
                Row(label=s["name"], value=f"{s['days']}d stale")

    n = len(repos)
    a = grades.get("A", 0)
    b = grades.get("B", 0)
    c = grades.get("C", 0)
    d = grades.get("D", 0)
    f_g = grades.get("F", 0)
    summary = (
        f"Glama Fleet: {n} repos tracked — "
        f"{a}A/{b}B/{c}C/{d}D/{f_g}F. "
        f"{len(worst_tools)} worst tools, {len(stale_repos)} stale."
    )
    return ToolResult(content=summary, structured_content=app)


@mcp.tool(app=True)
async def show_glama_repo_card(repo_name: str) -> ToolResult:
    """Show per-repo Glama score breakdown as a rich Prefab card.

    Displays overall grade, TDQS scores, coherence dimensions,
    maintenance grade, and per-tool scores for a single repo.

    Args:
        repo_name: Fleet repo name (e.g. "email-mcp").

    ## Return Format
    ToolResult with PrefabApp card and plain-text fallback.

    ## Examples
    await show_glama_repo_card("email-mcp")
    """
    repo = get_repo_score(repo_name)
    if not repo:
        return ToolResult(
            content=f"Repo '{repo_name}' not found. Run a refresh first.",
        )

    grade = repo.get("overall_grade") or "?"
    score = repo.get("overall_score")
    score_str = f"{score:.2f}" if score is not None else "?"

    with PrefabApp(title=f"Glama: {repo_name} ({grade})") as app:
        Heading("Summary")
        Row(label="Overall Grade", value=grade)
        Row(label="Overall Score", value=score_str)
        Row(label="TDQS Mean", value=f"{repo.get('tdqs_mean', '?'):.2f}")
        Row(label="TDQS Min", value=f"{repo.get('tdqs_min', '?'):.2f}")
        Row(label="Coherence", value=repo.get("coherence_grade") or "?")
        Row(label="Maintenance", value=repo.get("maintenance_grade") or "?")
        Row(label="Profile", value=f"{repo.get('profile_completion', 0)}%")
        Row(
            label="Latest Release",
            value=repo.get("latest_release") or "?",
        )

        tools = repo.get("tools", [])
        Heading(f"Tools ({len(tools)}) — Worst First")
        for t in sorted(tools, key=lambda x: x.get("score", 5))[:20]:
            t_grade = t.get("grade") or "?"
            t_score = t.get("score")
            t_score_str = f"{t_score:.1f}" if t_score is not None else "?"
            Row(
                label=t.get("name", "?"),
                value=f"{t_score_str}/5 [{t_grade}]",
            )

    summary = (
        f"{repo_name}: {grade} ({score_str}), "
        f"{len(tools)} tools, "
        f"μ={repo.get('tdqs_mean', '?'):.2f}"
    )
    return ToolResult(content=summary, structured_content=app)


@mcp.prompt()
def glama_improvement_plan(repo_name: str) -> str:
    """Generate a docstring improvement plan for a repo from its Glama scores."""
    repo = get_repo_score(repo_name)
    if not repo:
        return f"Repo '{repo_name}' not found. Run a refresh first."
    lines = [
        f"# Glama improvement plan: {repo_name}",
        (
            f"Current grade: {repo.get('overall_grade', '?')} "
            f"(score: {repo.get('overall_score', '?')})"
        ),
        (
            f"TDQS mean: {repo.get('tdqs_mean', '?')} | "
            f"TDQS min: {repo.get('tdqs_min', '?')}"
        ),
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
        lines.append(
            f"- **{t.get('name')}** ({t.get('grade', '?')}, "
            f"{t.get('score', '?')}/5)  -  {' | '.join(dims)}"
        )
    lines.extend([
        "",
        "### Fix plan",
        (
            "1. Fix the worst tool first (it pulls the whole server "
            "down via 60/40 mean/min formula)"
        ),
        "2. Add missing parameter descriptions via `Field(description=...)`",
        "3. Add behavioral warnings for destructive operations",
        "4. Add 'When to use' / 'When NOT to use' guidance",
        "5. Keep docstrings 80-250 words",
        "6. Make a release, push to PyPI, trigger 'Sync Server' on glama.ai",
    ])
    return "\n".join(lines)


@mcp.tool(annotations=_MUTATING)
async def glama_agentic_analyze(
    repo_name: str = "",
    ctx: Context | None = None,
) -> dict:
    """Analyze Glama scores with LLM sampling and generate fixable todos.

    Uses the connected LLM (via MCP ctx.sample) to intelligently analyze a
    repo's tool docstring scores and produce actionable fix tasks.

    Args:
        repo_name: Fleet repo name to analyze, or empty for fleet-wide.
        ctx: MCP context for sampling (auto-injected).

    Returns:
        success, repo_name, analysis (LLM output), todos (list).
    """
    if not ctx:
        return {
            "success": False,
            "error": "Sampling not available -- run from an MCP client with sampling support.",
            "recovery_options": [
                "Use glama_improvement_plan prompt instead",
                "Run glama_generate_repo_report for a static analysis",
            ],
        }

    if repo_name:
        repo = get_repo_score(repo_name)
        if not repo:
            return {"success": False, "error": f"Repo '{repo_name}' not found."}
        scope = f"repo '{repo_name}'"
        tools = sorted(
            repo.get("tools", []), key=lambda t: t.get("score", 5)
        )
        tool_list = "\n".join(
            f"- {t.get('name')}: {t.get('grade')}/{t.get('score')}/5 "
            f"(Purpose={t.get('purpose')}, Usage={t.get('usage_guidelines')}, "
            f"Behavior={t.get('behavior')}, Params={t.get('parameters')}, "
            f"Concise={t.get('conciseness')}, Complete={t.get('completeness')})"
            for t in tools
        )
    else:
        report = generate_report()
        scope = "entire fleet"
        repos_desc = "\n".join(
            f"- {r['name']}: {r.get('overall_grade')} (score: {r.get('overall_score')})"
            for r in report["repos"][:10]
        )
        tool_list = f"Fleet repos:\n{repos_desc}"

    prompt = (
        f"You are a Glama TDQS (Tool Definition Quality Score) analyst. "
        f"Analyze the following {scope} scores and produce:\n"
        f"1. A one-paragraph summary of the state of {scope}\n"
        f"2. The 5 most impactful fixes (specific, actionable)\n"
        f"3. Any pattern you see across tools (e.g., all missing "
        f"parameter descriptions, all too verbose)\n\n"
        f"Scores:\n{tool_list}\n\n"
        f"TDQS dimensions: Purpose, Usage Guidelines, Behavior, "
        f"Parameters, Conciseness, Completeness. Score = 60% mean + 40% min."
    )

    try:
        result = await ctx.sample(prompt)
        return {
            "success": True,
            "repo_name": repo_name or "fleet",
            "analysis": result,
            "message": f"Agentic analysis complete for {scope}.",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Sampling failed: {e}",
            "recovery_options": [
                "Ensure your MCP client supports sampling (Claude Desktop, Cursor)",
                "Fall back to glama_improvement_plan prompt",
            ],
        }


@mcp.tool(annotations=_MUTATING)
async def glama_generate_reports(repo_name: str = "") -> dict:
    """Generate markdown analysis reports for repos.

    Creates per-repo fix-todo reports in the reports/ directory,
    suitable for ingestion by IDE LLMs. If repo_name is empty,
    generates reports for all scored repos.

    Args:
        repo_name: Optional. If set, generate only for that repo.

    Returns:
        success, paths (list of generated file paths), count.
    """
    from glama_status_mcp.reporting import (
        write_all_repo_reports,
        write_repo_report,
    )

    if repo_name:
        path = write_repo_report(repo_name)
        paths = [path]
    else:
        paths = write_all_repo_reports()

    return {
        "success": True,
        "operation": "generate_reports",
        "data": {"paths": paths, "count": len(paths)},
        "message": f"Generated {len(paths)} reports in reports/.",
    }


@mcp.prompt()
def glama_fleet_analysis_prompt() -> str:
    """Generate a fleet-wide Glama analysis prompt for the connected LLM."""
    report = generate_report()
    repos = report["repos"]
    grades = report["grade_distribution"]
    stale = report["stale_repos"]

    repo_lines = "\n".join(
        f"- {r['name']}: {r.get('overall_grade')} "
        f"(score: {r.get('overall_score')}, "
        f"TDQS: \u03bc={r.get('tdqs_mean')}, min={r.get('tdqs_min')})"
        for r in repos
    )

    stale_lines = "\n".join(
        f"- {s['name']} ({s['days']} days stale)" for s in stale
    )

    return (
        f"# Fleet Glama Health Analysis\n\n"
        f"Repos tracked: {len(repos)}\n"
        f"Grade distribution: A={grades.get('A',0)}, B={grades.get('B',0)}, "
        f"C={grades.get('C',0)}, D={grades.get('D',0)}, F={grades.get('F',0)}\n\n"
        f"## All Repos (worst first)\n{repo_lines}\n\n"
        f"## Stale Repos\n{stale_lines or 'None'}\n\n"
        f"## Task\n"
        f"Analyze this fleet health snapshot. Identify:\n"
        f"1. The 3 repos that need the most urgent attention\n"
        f"2. Common docstring failure patterns across repos\n"
        f"3. A prioritized fix plan for the next sprint\n"
    )


def _init():
    from glama_status_mcp.models import FLEET_REPOS as _FR
    init_db()
    seed_fleet(_FR)


def main():
    _init()
    if "--http" in sys.argv:
        from pathlib import Path

        import uvicorn
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.staticfiles import StaticFiles

        app = FastAPI(title="glama-status-mcp")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

        mcp_asgi = mcp.http_app(path="/mcp")
        app.mount("/mcp", mcp_asgi)

        @app.get("/health")
        async def health():
            return {"status": "ok", "service": "glama-status-mcp"}

        @app.get("/api/repos")
        async def api_repos():
            return get_all_repo_scores()

        @app.get("/api/repos/{name}")
        async def api_repo(name: str):
            from fastapi.responses import JSONResponse
            repo = get_repo_score(name)
            if not repo:
                return JSONResponse(
                    {"error": "not found"}, status_code=404
                )
            return repo

        @app.get("/api/worst-tools")
        async def api_worst_tools(limit: int = 20):
            return get_worst_tools(limit)

        @app.post("/api/refresh")
        async def api_refresh():
            return await _do_refresh()

        @app.get("/api/history")
        async def api_history(limit: int = 10):
            return get_refresh_history(limit)

        @app.get("/api/report")
        async def api_report():
            return generate_report()

        @app.get("/api/deltas")
        async def api_deltas():
            return compute_deltas()

        @app.get("/api/reports/generate")
        async def api_reports(repo_name: str = ""):
            from glama_status_mcp.reporting import (
                write_all_repo_reports,
                write_repo_report,
            )
            if repo_name:
                path = write_repo_report(repo_name)
                return {"paths": [path], "count": 1}
            paths = write_all_repo_reports()
            return {"paths": paths, "count": len(paths)}

        @app.get("/api/llm/providers")
        async def api_llm_providers():
            from glama_status_mcp.llm import discover_providers
            providers = await discover_providers()
            return {
                "providers": [
                    {
                        "name": p.name,
                        "base_url": p.base_url,
                        "available": p.available,
                        "models": p.models,
                    }
                    for p in providers
                ]
            }

        @app.post("/api/chat")
        async def api_chat(request: dict):
            from glama_status_mcp.llm import chat as llm_chat
            msg = request.get("message", "")
            history = request.get("context", {}).get("history", [])
            sp = request.get("system_prompt", "")
            provider = request.get("provider", "ollama")
            model = request.get("model", "")
            base_url = request.get("base_url", "")
            api_key = request.get("api_key", "")

            messages: list[dict[str, str]] = []
            if sp:
                messages.append({"role": "system", "content": sp})
            for h in history:
                messages.append(h)
            messages.append({"role": "user", "content": msg})

            reply = await llm_chat(
                provider=provider,
                base_url=base_url,
                model=model,
                messages=messages,
                api_key=api_key,
            )
            return {"success": True, "reply": reply, "provider": provider}

        webapp_dir = (
            Path(__file__).resolve().parent.parent.parent / "webapp" / "dist"
        )
        if webapp_dir.exists():
            app.mount(
                "/", StaticFiles(directory=str(webapp_dir), html=True),
                name="webapp",
            )

        idx = sys.argv.index("--port") + 1 if "--port" in sys.argv else None
        port = int(sys.argv[idx]) if idx else 11072
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
