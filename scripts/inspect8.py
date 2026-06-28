"""Debug specific patterns."""
import httpx
import re
from bs4 import BeautifulSoup

resp = httpx.get(
    "https://glama.ai/mcp/servers/sandraschi/virtualization-mcp/score",
    follow_redirects=True, timeout=30,
    headers={"User-Agent": "glama-status-mcp/0.1"}
)
soup = BeautifulSoup(resp.text, "lxml")

# Find "Average" paragraph and its container
for p in soup.find_all("p"):
    txt = p.get_text(strip=True)
    if "Average" in txt:
        print(f"=== Average paragraph ===")
        print(f"  text: '{txt}'")
        parent = p.parent
        print(f"  parent: <{parent.name}> class={parent.get('class', '')}")
        grandparent = parent.parent if parent else None
        if grandparent:
            print(f"  grandparent: <{grandparent.name}> class={grandparent.get('class', '')}")
            print(f"  grandparent text: '{grandparent.get_text(strip=True)[:300]}'")
        break

# Find "Maintenance" span's parent structure
for span in soup.find_all("span"):
    txt = span.get_text(strip=True)
    if txt == "Maintenance":
        print(f"\n=== Maintenance span ===")
        parent = span.parent
        print(f"  parent: <{parent.name}> class={parent.get('class', '')}")
        print(f"  parent text: '{parent.get_text(strip=True)[:200]}'")
        grandparent = parent.parent if parent else None
        if grandparent:
            print(f"  grandparent: <{grandparent.name}> class={grandparent.get('class', '')}")
        break

# Find coherence sub-score labels
for label in ["Disambiguation", "Naming Consistency", "Tool Count"]:
    for el in soup.find_all(string=re.compile(f"^{re.escape(label)}")):
        txt = el.strip()
        p = el.parent
        print(f"\n=== {label} ===")
        print(f"  in <{p.name}> class={p.get('class', '')}")
        # Check parent for score
        parent = p.parent
        if parent:
            print(f"  parent: <{parent.name}> class={parent.get('class', '')}")
            print(f"  parent text: '{parent.get_text(strip=True)[:100]}'")
            # Check siblings
            for sib in parent.find_all(["span", "div"], recursive=False):
                sib_txt = sib.get_text(strip=True)
                if sib_txt and sib_txt != txt:
                    print(f"  sibling: <{sib.name}> class={sib.get('class', '')} text='{sib_txt[:30]}'")
        break  # Just first match
