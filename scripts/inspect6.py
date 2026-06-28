"""Debug coherence sub-scores, TDQS, and maintenance parsing."""
import httpx
import re
from bs4 import BeautifulSoup

resp = httpx.get(
    "https://glama.ai/mcp/servers/sandraschi/virtualization-mcp/score",
    follow_redirects=True, timeout=30,
    headers={"User-Agent": "glama-status-mcp/0.1"}
)
soup = BeautifulSoup(resp.text, "lxml")

# Find coherence section
coh = soup.find(string=re.compile(r'^Server Coherence$'))
if coh:
    section = coh.find_parent(["div", "section"])
    if section:
        print("=== Coherence section ===")
        # Print all descendant text
        for t in section.descendants:
            if t.string and t.string.strip():
                print(f"  '{t.string.strip()}' in <{t.parent.name}>")
        
        # Check for sub-score labels
        for label in ["Disambiguation", "Naming Consistency", "Tool Count", "Completeness"]:
            el = section.find(string=re.compile(f"^{re.escape(label)}"))
            if el:
                container = el.parent
                print(f"\n  {label}:")
                print(f"    container: <{container.name}> class={container.get('class', '')}")
                print(f"    container text: '{container.get_text(strip=True)}'")
                # Check siblings for the score
                ns = container.find_next_sibling()
                if ns:
                    print(f"    next sibling: <{ns.name}> class={ns.get('class', '')} text='{ns.get_text(strip=True)[:60]}'")
                # Check the parent for score
                parent = container.parent
                print(f"    parent text: '{parent.get_text(strip=True)[:80]}'")

# TDQS
tdqs = soup.find(string=re.compile(r'^Tool Definition Quality$'))
if tdqs:
    parent = tdqs.parent
    print(f"\n=== TDQS ===")
    print(f"  parent: <{parent.name}> class={parent.get('class', '')}")
    print(f"  parent text: '{parent.get_text(strip=True)[:200]}'")

# Maintenance
maint = soup.find(string=re.compile(r'^Maintenance$'))
if maint:
    parent = maint.parent
    print(f"\n=== Maintenance ===")
    print(f"  parent: <{parent.name}> class={parent.get('class', '')}")
    print(f"  parent text: '{parent.get_text(strip=True)[:100]}'")
