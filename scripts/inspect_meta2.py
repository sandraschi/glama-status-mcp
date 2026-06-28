"""Find coherence grade and maintenance grade."""
import httpx
import re
from bs4 import BeautifulSoup

resp = httpx.get(
    "https://glama.ai/mcp/servers/sandraschi/virtualization-mcp/score",
    follow_redirects=True, timeout=30,
    headers={"User-Agent": "glama-status-mcp/0.1"}
)
soup = BeautifulSoup(resp.text, "lxml")

# Find "Server Coherence" label and its siblings for grade
print("=== Server Coherence grade ===")
for span in soup.find_all("span"):
    txt = span.get_text(strip=True)
    if txt == "Server Coherence":
        print(f"Found: <{span.name}> class={span.get('class', '')}")
        parent = span.parent
        print(f"Parent: <{parent.name}> class={parent.get('class', '')}")
        print(f"Parent text: '{parent.get_text(strip=True)[:100]}'")
        # Check parent siblings for grade
        for sib in parent.find_next_siblings():
            stxt = sib.get_text(strip=True)
            m = re.search(r'\b[ABCDF]\b', stxt)
            if m:
                print(f"  Grade in sibling <{sib.name}>: '{stxt[:30]}' -> {m.group(0)}")
        # Also check parent's parent
        gp = parent.parent
        if gp:
            gptxt = gp.get_text(strip=True)
            m = re.search(r'\b[ABCDF]\b', gptxt)
            if m:
                print(f"  Grade in grandparent: '{m.group(0)}' in '{gptxt[:80]}'")
        break

# Find "Maintenance" label and its structure
print("\n=== Maintenance grade ===")
for span in soup.find_all("span"):
    txt = span.get_text(strip=True)
    if txt == "Maintenance":
        print(f"Found: <{span.name}> class={span.get('class', '')}")
        parent = span.parent
        print(f"Parent: <{parent.name}> class={parent.get('class', '')}")
        print(f"Parent text: '{parent.get_text(strip=True)[:100]}'")
        # Walk up 3 levels looking for grade
        cur = span
        for i in range(5):
            cur = cur.parent
            if cur:
                ctxt = cur.get_text(strip=True)
                m = re.search(r'\b[ABCDF]\b', ctxt)
                print(f"  Level {i+1}: <{cur.name}> class={cur.get('class', '')} {'-> grade: ' + m.group(0) if m else 'no grade'}")
                if m:
                    break
        break

# Also look for all checklist items (li elements containing a grade letter)
print("\n=== All checklist-like items with grades ===")
for li in soup.find_all(["li", "div"]):
    txt = li.get_text(strip=True)
    if not txt:
        continue
    m = re.search(r'\b[ABCDF]\b', txt)
    if m and any(label in txt for label in ["Server Coherence", "Disambiguation", "Maintenance", "Tool Definition", "Profile", "README", "glama.json"]):
        print(f"  <{li.name}> grade={m.group(0)} text='{txt[:100]}'")
