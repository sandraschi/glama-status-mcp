"""Find dimension scores in Glama page."""
import httpx
import re
from bs4 import BeautifulSoup

resp = httpx.get(
    "https://glama.ai/mcp/servers/sandraschi/virtualization-mcp/score",
    follow_redirects=True, timeout=30,
    headers={"User-Agent": "glama-status-mcp/0.1"}
)
soup = BeautifulSoup(resp.text, "lxml")

# Find all tool buttons and look for dimension data
for btn in soup.find_all("button"):
    classes = " ".join(btn.get("class", []))
    if "ULqjq" in classes:
        link = btn.find("a", href=re.compile(r"/tools/"))
        tool_name = link.get_text(strip=True) if link else "?"
        grades = btn.find_all(string=re.compile(r"^[ABCDF]$"))
        scores = btn.find_all("span", string=re.compile(r"\d\.\d/5"))
        
        # Look for dimensions in the button content
        btn_text = btn.get_text(strip=True)
        
        # Check for sibling div after button (maybe expanded detail)
        sibling = btn.find_next_sibling("div")
        detail_text = sibling.get_text(strip=True) if sibling else ""
        
        print(f"\nTool: {tool_name}")
        print(f"  Grades: {[g.strip() for g in grades]}")
        print(f"  Scores: {[s.get_text(strip=True) for s in scores]}")
        
        # Check each dimension label
        for dim in ["Purpose", "Usage Guidelines", "Behavior", "Parameters", "Conciseness", "Completeness"]:
            # Search in button and sibling
            for src_name, src in [("btn", btn), ("sibling", sibling)]:
                if src:
                    el = src.find(string=re.compile(f"^{re.escape(dim)}"))
                    if el:
                        parent = el.parent
                        txt = parent.get_text(strip=True) if parent else ""
                        print(f"  [{src_name}] {dim}: {txt[:60]}")
        if not detail_text:
            print(f"  No expanded detail found")
