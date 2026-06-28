import re
import asyncio
import json
from datetime import datetime, timezone
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from glama_status_mcp.config import GLAMA_BASE, SCRAPE_TIMEOUT, SCRAPE_DELAY
from glama_status_mcp.models import RepoScore, ToolScore, ServerCoherence

_USER_AGENT = "glama-status-mcp/0.1 (fleet monitor; sandraschi fleet; polite daily scrape of own repos)"


def _parse_grade(text: str) -> str:
    m = re.search(r'\b[ABCDF]\b', text)
    return m.group(0) if m else ""


def _parse_score(text: str) -> float:
    m = re.search(r'([\d.]+)\s*/\s*5', text)
    return float(m.group(1)) if m else 0.0


async def scrape_repo(name: str, namespace: str = "sandraschi") -> Optional[RepoScore]:
    """Fetch and parse a single Glama score page.
    
    Uses polite scraping: descriptive UA, delay handling, timeout.
    Falls back to BrightData proxy if GLAMA_USE_BRIGHTDATA=1 is set.
    Returns None if the page is not found (404) or unreachable.
    """
    import os
    use_brightdata = os.getenv("GLAMA_USE_BRIGHTDATA", "").lower() in ("1", "true", "yes")
    brightdata_token = os.getenv("GLAMA_BRIGHTDATA_TOKEN", "")

    url = f"{GLAMA_BASE}/{namespace}/{name}/score"
    headers = {"User-Agent": _USER_AGENT, "Accept": "text/html"}

    async with httpx.AsyncClient(timeout=SCRAPE_TIMEOUT, follow_redirects=True) as client:
        try:
            if use_brightdata and brightdata_token:
                proxy_url = f"http://brd-customer-hl_{brightdata_token}:@brd.superproxy.io:22225"
                resp = await client.get(url, headers=headers, proxies={"all://": proxy_url})
            else:
                resp = await client.get(url, headers=headers)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
        except Exception:
            return None

    return _parse_html(resp.text, name, namespace)


def _parse_html(html: str, name: str, namespace: str) -> RepoScore:
    soup = BeautifulSoup(html, "lxml")
    score = RepoScore(name=name, glama_namespace=namespace, glama_slug=name)

    # Profile completion %
    el = soup.find(string=re.compile(r'(\d+)%'))
    if el:
        m = re.search(r'(\d+)%', str(el))
        if m:
            score.profile_completion = int(m.group(1))

    # Latest release
    el = soup.find(string=re.compile(r'Latest release', re.I))
    if el and el.parent:
        m = re.search(r'v?[\d]+\.[\d]+\.[\d]+[^\s]*', el.parent.get_text(strip=True))
        if m:
            score.latest_release = m.group(0)

    # Server Coherence — sub-scores appear in checklist items near the top
    for label, attr in [
        ("Disambiguation", "disambiguation"),
        ("Naming Consistency", "naming_consistency"),
        ("Tool Count", "tool_count"),
        ("Completeness", "completeness"),
    ]:
        el = soup.find(string=re.compile(f"^{re.escape(label)}"))
        if el:
            container = el.parent
            if container:
                val = _parse_score(container.get_text(strip=True))
                if val > 0:
                    setattr(score.coherence, attr, val)
            # Walk up to find grade
            parent_section = el.find_parent(["div", "section", "li"])
            if parent_section and not score.coherence.grade:
                g = _parse_grade(parent_section.get_text(strip=True))
                if g:
                    score.coherence.grade = g

    # TDQS — "Average3.5/5 across9of9tools scored.Lowest: 2.4/5." (no space after Average)
    tdqs_p = soup.find("p", string=re.compile(r'Average'))
    if tdqs_p:
        txt = tdqs_p.get_text(strip=True)
        m_mean = re.search(r'Average([\d.]+)/5', txt)
        if m_mean:
            score.tdqs_mean = float(m_mean.group(1))
        m_min = re.search(r'Lowest:\s*([\d.]+)/5', txt)
        if m_min:
            score.tdqs_min = float(m_min.group(1))
            if score.tdqs_mean:
                overall = 0.6 * score.tdqs_mean + 0.4 * score.tdqs_min
                score.overall_score = round(overall, 2)
                score.overall_grade = (
                    "A" if overall >= 3.5 else
                    "B" if overall >= 3.0 else
                    "C" if overall >= 2.0 else
                    "D" if overall >= 1.0 else "F"
                )
        score.tdqs_grade = _parse_grade(txt)

    # Maintenance — find the grade letter near label
    maint_span = soup.find("span", string=re.compile(r'^Maintenance$'))
    if maint_span:
        container = maint_span.parent
        if container:
            score.maintenance_grade = _parse_grade(container.get_text(strip=True))

    # Per-tool cards — each tool is a <button> with a /tools/ link
    for btn in soup.find_all("button"):
        classes = " ".join(btn.get("class", []))
        if "ULqjq" not in classes:
            continue
        link = btn.find("a", href=re.compile(r"/tools/"))
        if not link:
            continue

        tool_name = link.get_text(strip=True)
        btn_text = btn.get_text(strip=True)
        tool = ToolScore(
            name=tool_name,
            grade=_parse_grade(btn_text),
            score=_parse_score(btn_text),
        )

        # Dimension scores live in the collapsed detail sibling
        detail = btn.find_next_sibling("div")
        if detail:
            for dim_label, attr in [
                ("Purpose", "purpose"),
                ("Usage Guidelines", "usage_guidelines"),
                ("Behavior", "behavior"),
                ("Parameters", "parameters"),
                ("Conciseness", "conciseness"),
                ("Completeness", "completeness"),
            ]:
                dim_el = detail.find(string=re.compile(f"^{re.escape(dim_label)}$"))
                if dim_el:
                    card = dim_el.find_parent("div", class_=lambda c: c and "gMBAYo" in str(c))
                    if card:
                        span = card.find("span", class_=lambda c: c and "czikZZ" in str(c))
                        if span:
                            setattr(tool, attr, _parse_score(span.get_text(strip=True)))

        if tool.score > 0 or tool.grade:
            score.tools.append(tool)

    # Fallback: compute overall from tool scores if TDQS not parsed
    if not score.tdqs_mean and score.tools:
        vals = [t.score for t in score.tools if t.score > 0]
        if vals:
            overall = 0.6 * (sum(vals) / len(vals)) + 0.4 * min(vals)
            score.overall_score = round(overall, 2)
            score.overall_grade = (
                "A" if overall >= 3.5 else
                "B" if overall >= 3.0 else
                "C" if overall >= 2.0 else
                "D" if overall >= 1.0 else "F"
            )

    return score
