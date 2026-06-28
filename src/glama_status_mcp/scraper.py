import re

import httpx
from bs4 import BeautifulSoup

from glama_status_mcp.config import GLAMA_BASE, SCRAPE_TIMEOUT
from glama_status_mcp.models import FleetRepo, RepoScore, ToolScore

_USER_AGENT = (
    "glama-status-mcp/0.1 (MCP fleet score tracker; Daily score scrape)"
)


def _parse_grade(text: str) -> str:
    # Match standalone grade letter A/B/C/D/F adjacent to tool name suffix
    m = re.search(r'[a-z0-9_]([ABCDF])(?:\s|[0-9]|$)', text)
    if m:
        return m.group(1)
    m = re.search(r'(?<![a-zA-Z0-9])[ABCDF](?![a-zA-Z0-9])', text)
    return m.group(0) if m else ""


def _parse_score(text: str) -> float:
    m = re.search(r'([\d.]+)\s*/\s*5', text)
    return float(m.group(1)) if m else 0.0


async def scrape_repo(name: str, namespace: str = "sandraschi", slug: str = "") -> RepoScore | None:
    """Fetch and parse a single Glama score page.
    
    Uses polite scraping: descriptive UA, delay handling, timeout.
    Falls back to BrightData proxy if GLAMA_USE_BRIGHTDATA=1 is set.
    Returns None if the page is not found (404) or unreachable.
    """
    import os
    use_brightdata = os.getenv("GLAMA_USE_BRIGHTDATA", "").lower() in ("1", "true", "yes")
    brightdata_token = os.getenv("GLAMA_BRIGHTDATA_TOKEN", "")
    path = slug or name

    url = f"{GLAMA_BASE}/{namespace}/{path}/score"
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

    # Grade badges  -  use the specific badge span class
    for badge in soup.find_all("span", class_=lambda c: c and "kIIaya" in str(c)):
        badge_text = badge.get_text(strip=True)
        if badge_text not in ("A", "B", "C", "D", "F"):
            continue
        # Find the label text that appears before this badge
        parent = badge.parent
        if parent:
            ptext = parent.get_text(strip=True)
            if ptext.startswith("Server Coherence") or "Server Coherence" in ptext:
                score.coherence.grade = badge_text
            elif ptext.startswith("Maintenance") or "Maintenance" in ptext:
                score.maintenance_grade = badge_text
            elif ptext.startswith("Tool Definition Quality") or "Tool Definition Quality" in ptext:
                score.tdqs_grade = badge_text

    # Server Coherence sub-scores
    coherence_labels = {"Disambiguation", "Naming Consistency", "Tool Count", "Completeness"}
    for span in soup.find_all("span", class_=lambda c: c and "czikZZ" in str(c)):
        st = span.get_text(strip=True)
        m = re.search(r'^(\d+(?:\.\d+)?)\s*/\s*5$', st)
        if not m:
            continue
        parent = span.parent
        if not parent:
            continue
        parent_text = parent.get_text(strip=True)
        for label in coherence_labels:
            if label in parent_text:
                val = float(m.group(1))
                attr_map = {
                    "Disambiguation": "disambiguation",
                    "Naming Consistency": "naming_consistency",
                    "Tool Count": "tool_count",
                    "Completeness": "completeness",
                }
                setattr(score.coherence, attr_map[label], val)
                break

    # TDQS  -  find element containing both "Average" and "Lowest"
    for el in soup.find_all(["p", "div", "span"]):
        txt = el.get_text(strip=True)
        if "Average" in txt and "Lowest" in txt:
            m_mean = re.search(r'Average\s*([\d.]+)\s*/?\s*5', txt)
            m_min = re.search(r'Lowest:\s*([\d.]+)\s*/?\s*5', txt)
            if m_mean:
                score.tdqs_mean = float(m_mean.group(1))
            if m_min:
                score.tdqs_min = float(m_min.group(1))
            if score.tdqs_mean and score.tdqs_min:
                overall = 0.6 * score.tdqs_mean + 0.4 * score.tdqs_min
                score.overall_score = round(overall, 2)
                score.overall_grade = (
                    "A" if overall >= 3.5 else
                    "B" if overall >= 3.0 else
                    "C" if overall >= 2.0 else
                    "D" if overall >= 1.0 else "F"
                )
            break

    # Per-tool cards  -  each tool is a <button> with a /tools/ link
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


async def discover_repos(author: str = "sandraschi") -> list[FleetRepo]:
    """Scrape the Glama author page to find all registered MCP servers.

    Fetches https://glama.ai/mcp/servers?query=author%3A{author}
    and extracts repo names from the server card links.
    """
    url = f"{GLAMA_BASE}?query=author%3A{author}"
    headers = {"User-Agent": _USER_AGENT, "Accept": "text/html"}

    async with httpx.AsyncClient(
        timeout=SCRAPE_TIMEOUT, follow_redirects=True
    ) as client:
        try:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
        except Exception:
            return []

    soup = BeautifulSoup(resp.text, "lxml")
    repos: list[FleetRepo] = []
    seen: set[str] = set()

    # Server cards link to /mcp/servers/{author}/{repo}
    for a_tag in soup.find_all(
        "a", href=re.compile(rf"/mcp/servers/{re.escape(author)}/[^/]+/?$")
    ):
        href = a_tag.get("href", "")
        parts = href.rstrip("/").split("/")
        if len(parts) >= 4:
            name = parts[-1]
            if name and name not in seen:
                seen.add(name)
                repos.append(
                    FleetRepo(name=name, glama_author=author)
                )

    return repos
