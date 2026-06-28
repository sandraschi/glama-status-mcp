"""Find how tool names are structured in Glama page."""
import httpx
import re
from bs4 import BeautifulSoup

resp = httpx.get(
    "https://glama.ai/mcp/servers/sandraschi/virtualization-mcp/score",
    follow_redirects=True, timeout=30,
    headers={"User-Agent": "glama-status-mcp/0.1"}
)
soup = BeautifulSoup(resp.text, "lxml")

# Print all <a> tags that link to tool pages
print("=== Tool links ===")
for a in soup.find_all("a", href=True):
    href = a["href"]
    if "/tools/" in href:
        txt = a.get_text(strip=True)
        classes = " ".join(a.get("class", []))
        print(f"  href={href[-40:]}")
        print(f"  text='{txt}'")
        print(f"  class='{classes[:50]}'")
        # Check parent container
        parent = a.parent
        if parent:
            pc = " ".join(parent.get("class", []))
            print(f"  parent <{parent.name}> class='{pc[:50]}'")
            grandparent = parent.parent
            if grandparent:
                gc = " ".join(grandparent.get("class", []))
                print(f"  grandparent <{grandparent.name}> class='{gc[:50]}'")
                # Check if there's a grade span in grandparent
                grades = grandparent.find_all(string=re.compile(r"^[ABCDF]$"))
                scores = grandparent.find_all("span", string=re.compile(r"\d\.\d/5"))
                if grades or scores:
                    print(f"    grades: {[g.strip() for g in grades]}")
                    print(f"    scores: {[s.get_text(strip=True) for s in scores]}")
                # Check dimension labels
                for dim in ["Purpose", "Usage", "Behavior", "Params", "Conciseness", "Completeness"]:
                    de = grandparent.find(string=re.compile(f"^{dim}"))
                    if de:
                        dp = de.parent
                        dt = dp.get_text(strip=True) if dp else ""
                        print(f"    {dim}: {dt[:60]}")
        print()
