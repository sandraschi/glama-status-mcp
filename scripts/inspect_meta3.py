"""Find all checklist items with labels and grades."""
import httpx
import re
from bs4 import BeautifulSoup

resp = httpx.get(
    "https://glama.ai/mcp/servers/sandraschi/virtualization-mcp/score",
    follow_redirects=True, timeout=30,
    headers={"User-Agent": "glama-status-mcp/0.1"}
)
soup = BeautifulSoup(resp.text, "lxml")

# Find "Server Quality Checklist" section
check_header = soup.find(string=re.compile(r"Server Quality Checklist"))
if check_header:
    section = check_header.find_parent(["div", "section"])
    if section:
        print("=== Checklist section structure ===")
        # Print direct children and their text
        for child in section.children:
            if hasattr(child, 'name') and child.name:
                txt = child.get_text(strip=True)[:120]
                print(f"  <{child.name}> class={child.get('class', '')[:2] if child.get('class') else ''} '{txt}'")

# Look for specific label + grade patterns in the page
print("\n=== Labels with grades ===")
for label in ["Server Coherence", "Tool Definition Quality", "Maintenance", "Profile completion", "Has README", "Has valid"]:
    for el in soup.find_all(string=re.compile(label)):
        parent = el.parent
        ptext = parent.get_text(strip=True)[:100]
        m = re.search(r'\b[ABCDF]\b', ptext)
        if m:
            print(f"  '{label}' grade={m.group(0)} in '{ptext}'")
            break

# Check the overall grade area around the Server Quality Checklist header  
print("\n=== Checklist header container ===")
hdr = soup.find(string=re.compile(r"Server Quality Checklist"))
if hdr:
    ancestor = hdr.find_parent(["div", "section"])
    if ancestor:
        # Walk siblings
        for sib in ancestor.find_next_siblings():
            stxt = sib.get_text(strip=True)[:100]
            if stxt.strip():
                print(f"  Sibling <{sib.name}>: '{stxt}'")
