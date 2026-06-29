"""Per-repo markdown report generation for IDE LLM consumption.

Can optionally use a configured local/cloud LLM for per-tool analysis
when use_llm=True. Falls back to template-based reports when no LLM
is available.
"""

from datetime import UTC, datetime
from pathlib import Path

from glama_status_mcp.database import generate_report, get_repo_score

REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


async def _llm_analysis(
    repo_name: str, tools: list[dict]
) -> str | None:
    """Call the configured LLM to analyze tool scores.

    Discovers available providers (Ollama/LM Studio/OpenAI), picks
    the first available one, and sends the tool scores for analysis.
    Returns markdown-formatted analysis or None if no LLM available.
    """
    try:
        from glama_status_mcp.llm import chat, discover_providers
        providers = await discover_providers()
        provider = next((p for p in providers if p.available), None)
        if not provider:
            return None

        model = provider.models[0] if provider.models else "default"
        scores = "\n".join(
            f"- {t.get('name')}: {t.get('grade')}/{t.get('score')}/5"
            f"  Purpose={t.get('purpose')}, Usage={t.get('usage_guidelines')},"
            f"  Behavior={t.get('behavior')}, Params={t.get('parameters')},"
            f"  Concise={t.get('conciseness')}, Complete={t.get('completeness')}"
            for t in tools[:20]
        )

        prompt = (
            "You are a Glama TDQS docstring analysis tool. "
            f"Analyze these tool scores for repo '{repo_name}'.\n"
            "TDQS formula: score = 60% mean + 40% minimum.\n"
            "Dimensions: Purpose(25%), Usage(20%), Behavior(20%), "
            "Params(15%), Conciseness(10%), Completeness(10%).\n\n"
            "For each tool, identify specific failing dimensions "
            "and write 1-2 sentences on what to fix.\n"
            "Then give 3 overall recommendations for the repo.\n\n"
            f"Tools:\n{scores}"
        )

        result = await chat(
            provider=provider.name,
            base_url=provider.base_url,
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return result
    except Exception:
        return None


async def generate_repo_report(
    repo_name: str, use_llm: bool = True
) -> str:
    """Generate a detailed per-repo markdown report with fix todos.

    When use_llm=True and a local/cloud LLM is reachable, includes
    AI-powered per-tool analysis. Falls back to template when no
    LLM is available.
    """
    repo = get_repo_score(repo_name)
    if not repo:
        return f"# {repo_name}\n\nNo data. Run a refresh first.\n"

    grade = repo.get("overall_grade") or "?"
    score = repo.get("overall_score") or 0
    tools = sorted(
        repo.get("tools", []), key=lambda t: t.get("score", 5)
    )

    lines = [
        f"# Glama Analysis: {repo_name}",
        "",
        f"**Grade:** {grade} | **Score:** {score:.2f}/5",
        (
            f"**TDQS Mean:** {repo.get('tdqs_mean', '?'):.2f}"
            f" | **Min:** {repo.get('tdqs_min', '?'):.2f}"
        ),
        (
            f"**Coherence:** {repo.get('coherence_grade', '?')}"
            f" | **Maintenance:** {repo.get('maintenance_grade', '?')}"
        ),
        (
            f"**Profile:** {repo.get('profile_completion', 0)}%"
            f" | **Release:** {repo.get('latest_release', '?')}"
        ),
        f"**Generated:** {datetime.now(UTC).isoformat()[:19]}",
        "",
        "---",
        "",
        "## Tool-by-Tool Breakdown",
        "",
        "| # | Tool | Grade | Score | Purpose | Usage | Behavior | Params | Concise | Complete |",
        "|---|------|-------|-------|---------|-------|----------|--------|---------|----------|",
    ]

    for i, t in enumerate(tools, 1):
        ns = repo.get("glama_namespace", "sandraschi")
        tool_url = (
            f"https://glama.ai/mcp/servers/{ns}"
            f"/{repo_name}/tools/{t.get('name')}"
        )
        lines.append(
            f"| {i} | [{t.get('name')}]({tool_url}) "
            f"| {t.get('grade', '?')} | {t.get('score', 0):.1f} "
            f"| {t.get('purpose', 0):.1f} | {t.get('usage_guidelines', 0):.1f} "
            f"| {t.get('behavior', 0):.1f} | {t.get('parameters', 0):.1f} "
            f"| {t.get('conciseness', 0):.1f} | {t.get('completeness', 0):.1f} |"
        )

    # LLM analysis section
    llm_text = None
    llm_source = None
    if use_llm:
        llm_text = await _llm_analysis(repo_name, tools)
        if llm_text:
            llm_source = "LLM"

    if llm_text:
        lines.extend([
            "",
            "---",
            "",
            f"## AI Analysis ({llm_source})",
            "",
            llm_text,
        ])
    else:
        # Template-based fix todos
        lines.extend([
            "",
            "---",
            "",
            "## Fix Todos (priority order)",
            "",
        ])
        priority = 1
        for t in tools:
            dims = []
            dim_map = {
                "Purpose": "purpose",
                "Usage Guidelines": "usage_guidelines",
                "Behavior": "behavior",
                "Parameters": "parameters",
                "Conciseness": "conciseness",
                "Completeness": "completeness",
            }
            for label, attr in dim_map.items():
                val = t.get(attr, 0)
                if val < 3:
                    dims.append(f"{label} ({val:.1f}/5)")
            if dims:
                lines.append(
                    f"{priority}. **{t.get('name')}**"
                    f" ({t.get('grade', '?')}, {t.get('score', 0):.1f}/5)"
                    f" -- {', '.join(dims)}"
                )
                priority += 1
        if priority == 1:
            lines.append(
                "No tool below 3.0 on any dimension."
            )

    lines.extend([
        "",
        "---",
        "",
        "## Fix Quick Reference",
        "",
        "1. Add `Field(description=...)` to every undocumented parameter",
        "2. Add 'When to use' / 'When NOT to use' guidance to docstrings",
        "3. Add behavioral warnings for destructive/mutating operations",
        "4. Keep docstrings 80-250 words",
        "5. Add `## Return Format`, `## Examples` sections per fleet standard",
        "6. Make a release, push to PyPI, trigger 'Sync Server' on glama.ai",
        "",
        "Generated by glama-status-mcp.",
    ])

    return "\n".join(lines)


async def write_repo_report(
    repo_name: str, use_llm: bool = True
) -> str:
    """Write a repo report to reports/{repo}.md and return path."""
    report = await generate_repo_report(repo_name, use_llm=use_llm)
    path = REPORTS_DIR / f"{repo_name}.md"
    path.write_text(report, encoding="utf-8")
    return str(path)


def generate_fleet_report() -> str:
    """Generate a fleet-wide markdown report with all repos."""
    data = generate_report()
    repos = data["repos"]
    deltas = data["deltas"]
    worst_tools = data["worst_tools_fleet"]
    stale = data["stale_repos"]

    lines = [
        "# Glama Fleet Analysis Report",
        f"Generated: {data['generated_at'][:19]}",
        f"Repos tracked: {data['total_repos']}",
        "",
        "## Grade Distribution",
    ]

    gd = data["grade_distribution"]
    lines.append(
        f"A: {gd.get('A', 0)} | B: {gd.get('B', 0)} | C: {gd.get('C', 0)} "
        f"| D: {gd.get('D', 0)} | F: {gd.get('F', 0)}"
    )

    lines.extend(["", "---", "", "## All Repos (worst first)", ""])

    for r in repos:
        tl = r.get("tools", [])
        worst = (
            min(tl, key=lambda t: t.get("score", 5)) if tl else None
        )
        wn = worst["name"] if worst else "-"
        ws = f"{worst['score']:.1f}" if worst else "-"
        lines.append(
            f"- **{r['name']}** {r.get('overall_grade') or '?'} "
            f"(score: {r.get('overall_score') or '?'}, "
            f"TDQS: \u03bc={r.get('tdqs_mean') or '?'}, "
            f"min={r.get('tdqs_min') or '?'}, "
            f"tools: {len(tl)}"
            f"{', worst: ' + wn + ' (' + ws + ')' if worst else ''})"
        )

    if deltas:
        changed = [
            d for d in deltas
            if d.get("score_change") and d["score_change"] != 0
        ]
        if changed:
            lines.extend(["", "---", "", "## Score Changes", ""])
            for d in sorted(
                changed,
                key=lambda x: abs(x["score_change"] or 0),
                reverse=True,
            ):
                arrow = (
                    "\u25b2"
                    if (d["score_change"] or 0) > 0
                    else "\u25bc"
                )
                lines.append(
                    f"- {d['repo_name']}: {d['previous_score']}"
                    f" \u2192 {d['current_score']}"
                    f" ({arrow}{d['score_change']:+.2f})"
                )

    if stale:
        lines.extend(["", "---", "", "## Stale Repos (>7 days)", ""])
        for s in stale:
            lines.append(f"- {s['name']} ({s['days']} days)")

    if worst_tools:
        lines.extend(
            ["", "---", "", "## Worst Tools Fleet-Wide", ""]
        )
        for t in worst_tools[:10]:
            lines.append(
                f"- {t['tool_name']} ({t['repo_name']}): "
                f"{t['tool_score']}/5 [{t['tool_grade']}]"
            )

    mk = "\n".join(lines)
    fleet_path = REPORTS_DIR / "fleet-report.md"
    fleet_path.write_text(mk, encoding="utf-8")
    return str(fleet_path)


async def write_all_repo_reports(
    use_llm: bool = True,
) -> list[str]:
    """Generate reports/ for every scored repo. Returns list of paths."""
    repos = generate_report()["repos"]
    paths = []
    for r in repos:
        p = await write_repo_report(r["name"], use_llm=use_llm)
        paths.append(p)
    fleet_p = generate_fleet_report()
    paths.append(fleet_p)
    return paths
