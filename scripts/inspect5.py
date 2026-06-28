"""Find exact dimension score structure."""
import httpx
import re
from bs4 import BeautifulSoup

resp = httpx.get(
    "https://glama.ai/mcp/servers/sandraschi/virtualization-mcp/score",
    follow_redirects=True, timeout=30,
    headers={"User-Agent": "glama-status-mcp/0.1"}
)
soup = BeautifulSoup(resp.text, "lxml")

# Find the proxmox tool button and its detail sibling
for btn in soup.find_all("button"):
    classes = " ".join(btn.get("class", []))
    if "ULqjq" in classes:
        link = btn.find("a", href=re.compile(r"/tools/"))
        if not link:
            continue
        tool_name = link.get_text(strip=True)
        if tool_name != "proxmox_management":
            # Check all tools but focus on proxmox
            pass
        
        sibling = btn.find_next_sibling("div")
        if sibling:
            # Print full HTML of sibling for proxmox
            if tool_name == "proxmox_management":
                print(f"=== HTML for {tool_name} detail ===")
                print(sibling.prettify()[:3000])
            
            # Find score patterns in sibling
            scores_in_sibling = sibling.find_all(string=re.compile(r"\d/5"))
            print(f"\n{tool_name} sibling scores:")
            for s in scores_in_sibling:
                p = s.parent
                txt = p.get_text(strip=True) if p else s.strip()
                print(f"  '{s.strip()}' in <{p.name}> parent text: {txt[:80]}")
            
            # Also check for 1-5 numbers near dimension labels
            for dim in ["Purpose", "Usage Guidelines", "Behavior", "Parameters", "Conciseness", "Completeness"]:
                dim_el = sibling.find(string=re.compile(f"^{re.escape(dim)}"))
                if dim_el:
                    # Get the parent element and look for nearby score
                    parent = dim_el.parent
                    full_text = parent.get_text(strip=True)
                    # Find a number pattern like "4/5" in the text
                    m = re.search(r'(\d)/5', full_text)
                    if m:
                        print(f"  {dim}: {m.group(0)} (from '{full_text[:60]}')")
