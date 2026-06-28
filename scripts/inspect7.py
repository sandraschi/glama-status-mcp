"""Debug coherence sub-scores and TDQS."""
import httpx
import re
from bs4 import BeautifulSoup

resp = httpx.get(
    "https://glama.ai/mcp/servers/sandraschi/virtualization-mcp/score",
    follow_redirects=True, timeout=30,
    headers={"User-Agent": "glama-status-mcp/0.1"}
)
soup = BeautifulSoup(resp.text, "lxml")

# Find all "4/5" type patterns and their context
print("=== All score patterns ===")
for el in soup.find_all(string=re.compile(r'\d\s*/\s*5')):
    txt = el.strip() if el else ""
    if not txt:
        continue
    p = el.parent
    path = []
    cur = el
    for _ in range(4):
        if cur.parent:
            path.append(f"<{cur.parent.name}>")
            cur = cur.parent
        else:
            break
    print(f"  '{txt[:20]}' in {' > '.join(reversed(path))}")

# TDQS - look for "Average" text
print("\n=== Average/Lowest patterns ===")
for el in soup.find_all(string=re.compile(r'Average|Lowest')):
    p = el.parent
    print(f"  '{el.strip()[:60]}' in <{p.name}> class={p.get('class','')}")

# Maintenance
print("\n=== Maintenance patterns ===")
for el in soup.find_all(string=re.compile(r'Maintenance')):
    p = el.parent
    print(f"  '{el.strip()[:60]}' in <{p.name}> class={p.get('class','')}")

# Look for "Score Badge" section which has the grade table
print("\n=== Score Badge section ===")
badge = soup.find(string=re.compile(r'Score Badge'))
if badge:
    section = badge.find_parent(["div", "section"])
    if section:
        print(section.get_text(strip=True)[:500])
