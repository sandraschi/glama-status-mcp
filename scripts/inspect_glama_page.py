"""Inspect Glama score page structure to debug scraper."""
import httpx
import re
from bs4 import BeautifulSoup

resp = httpx.get(
    "https://glama.ai/mcp/servers/sandraschi/virtualization-mcp/score",
    follow_redirects=True,
    timeout=30,
    headers={"User-Agent": "glama-status-mcp/0.1"}
)
soup = BeautifulSoup(resp.text, "lxml")

# Find all section-like elements
for tag in ["div", "section", "article", "li"]:
    els = soup.find_all(tag, class_=re.compile(r"sc-", re.I))
    if els:
        print(f"\n=== {tag} with sc- class ({len(els)} found) ===")
        for el in els[:5]:
            classes = " ".join(el.get("class", []))
            text = el.get_text(strip=True)[:150]
            print(f"  [{classes[:60]}] {text[:120]}")

# Check for tool score items
print("\n=== Looking for score-related text patterns ===")
for pattern in ["proxmox", "info_tools", "vm_management", "sandbox", "C\n    2.4", "A\n    4.8"]:
    found = soup.find_all(string=re.compile(re.escape(pattern), re.I))
    for f in found[:2]:
        p = f.parent
        tag = p.name if p else "?"
        classes = " ".join(p.get("class", [])) if p else ""
        print(f"  Found '{pattern}' in <{tag} class='{classes[:50]}'>")

# Print all h3 and following siblings
print("\n=== All h3/h4 elements ===")
for h in soup.find_all(["h3", "h4"]):
    txt = h.get_text(strip=True)
    if len(txt) > 2:
        classes = " ".join(h.get("class", []))
        print(f"  <{h.name} class='{classes[:40]}'> {txt[:80]}")
        # Check next sibling for tool data
        ns = h.find_next_sibling()
        if ns:
            nstxt = ns.get_text(strip=True)[:100] if ns.name else "(text node)"
            print(f"    next: <{ns.name}> {nstxt}")

# Check for the overall score
print("\n=== Looking for score value ===")
score_els = soup.find_all(string=re.compile(r"\d\.\d/5"))
for s in score_els[:10]:
    p = s.parent
    classes = " ".join(p.get("class", [])) if p else ""
    print(f"  {s.strip()[:40]}  in <{p.name} class='{classes[:40]}'>")
