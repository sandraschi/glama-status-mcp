"""Debug coherence structure for scraping."""
import httpx
import re
from bs4 import BeautifulSoup

resp = httpx.get(
    "https://glama.ai/mcp/servers/sandraschi/virtualization-mcp/score",
    follow_redirects=True, timeout=30,
    headers={"User-Agent": "glama-status-mcp/0.1"}
)
soup = BeautifulSoup(resp.text, "lxml")

# Find "Disambiguation" and walk up/down the tree
el = soup.find(string=re.compile(r"^Disambiguation$"))
if el:
    print(f"Label element: '{el.strip()}'")
    print(f"Parent: <{el.parent.name}> class={el.parent.get('class', '')}")
    p = el.parent
    print(f"  parent text: '{p.get_text(strip=True)}'")
    # Siblings
    for sib in p.find_next_siblings():
        print(f"  sibling: <{sib.name}> class={sib.get('class', '')} text='{sib.get_text(strip=True)[:30]}'")
    # Grandparent
    gp = p.parent
    print(f"Grandparent: <{gp.name}> class={gp.get('class', '')}")
    print(f"  gp text: '{gp.get_text(strip=True)[:80]}'")
    # Great grandparent
    ggp = gp.parent
    print(f"GGP: <{ggp.name}> class={ggp.get('class', '')}")
    # Search for score span in grandparent
    for span in gp.find_all("span"):
        st = span.get_text(strip=True)
        if re.search(r'\d\s*/\s*5', st):
            print(f"  SCORE SPAN in GP: '{st}' at <{span.name}> class={span.get('class', '')}")

    # Search for score in great grandparent
    for span in ggp.find_all("span"):
        st = span.get_text(strip=True)
        if re.search(r'\d\s*/\s*5', st):
            print(f"  SCORE SPAN in GGP: '{st}' at <{span.name}> class={span.get('class', '')}")

    # Also try finding span.czikZZ near the label
    for span in soup.find_all("span", class_=lambda c: c and "czikZZ" in str(c)):
        st = span.get_text(strip=True)
        if re.search(r'^\d\s*/\s*5$', st):
            # Check if this is near our label (within same li or checklist item)
            ancestor_li = span.find_parent(["li", "div"])
            label_in_ancestor = ancestor_li.find(string=re.compile(r"^Disambiguation$")) if ancestor_li else None
            if label_in_ancestor:
                print(f"  FOUND via czikZZ: '{st}' in same container")

# Check all czikZZ spans and their context
print("\n=== All czikZZ spans with X/5 ===")
for span in soup.find_all("span", class_=lambda c: c and "czikZZ" in str(c)):
    st = span.get_text(strip=True)
    if re.search(r'\d\s*/\s*5', st):
        parent = span.parent
        print(f"  '{st}' in <{parent.name}> class={parent.get('class', '')}")
        print(f"    parent text: '{parent.get_text(strip=True)[:60]}'")
        gp = parent.parent if parent else None
        if gp:
            print(f"    grandparent: <{gp.name}> class={gp.get('class', '')}")
