"""Find exactly how labels and grades relate."""
import httpx
import re
from bs4 import BeautifulSoup

resp = httpx.get(
    "https://glama.ai/mcp/servers/sandraschi/virtualization-mcp/score",
    follow_redirects=True, timeout=30,
    headers={"User-Agent": "glama-status-mcp/0.1"}
)
soup = BeautifulSoup(resp.text, "lxml")

# Find the big checklist div
checklist = soup.find("div", class_=lambda c: c and "koremC" in str(c) and "jDOzgL" in str(c))
if checklist:
    text = checklist.get_text(strip=True)
    print(f"Checklist text length: {len(text)}")
    # Find all labels and their following grades
    for label in ["Server Coherence", "Tool Definition Quality", "Maintenance", 
                  "Has a Glama release", "Has README", "Has valid glama.json",
                  "Author verified", "No recent usage", "No related servers"]:
        idx = text.find(label)
        if idx >= 0:
            snippet = text[idx:idx+80]
            print(f"  '{label}' -> '{snippet}'")
            
    # Now find Maintenance specifically
    print("\n=== Maintenance context ===")
    for span in soup.find_all("span"):
        if span.get_text(strip=True) == "Maintenance":
            print(f"Span: <{span.name}> class={span.get('class', '')}")
            # Walk up to find the checklist div
            ancestor = span.find_parent("div", class_=lambda c: c and "koremC" in str(c))
            if ancestor:
                atxt = ancestor.get_text(strip=True)
                idx = atxt.find("Maintenance")
                print(f"In checklist: '{atxt[idx:idx+60]}'")
            # Walk up looking for grade
            cur = span
            for i in range(6):
                cur = cur.parent
                if cur:
                    ctxt = cur.get_text(strip=True)
                    m = re.search(r'\b[ABCDF]\b', ctxt)
                    print(f"  Level {i+1}: <{cur.name}> class={str(cur.get('class', ''))[:40]} -> '{ctxt[:80]}'")
                    if m and i > 0:
                        print(f"    GRADE FOUND: {m.group(0)}")
                        break

# Also search for all text patterns like "MaintenanceX" where X is a grade
print("\n=== Raw text search ===")
body = soup.get_text(strip=True)
for m in re.finditer(r'(Maintenance|Server Coherence|Tool Definition Quality)\s*([ABCDF])\s', body):
    print(f"  '{m.group(1)}' grade={m.group(2)}")
