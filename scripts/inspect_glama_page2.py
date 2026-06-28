"""Deeper inspection of Glama page structure."""
import httpx
import re
from bs4 import BeautifulSoup

resp = httpx.get(
    "https://glama.ai/mcp/servers/sandraschi/virtualization-mcp/score",
    follow_redirects=True, timeout=30,
    headers={"User-Agent": "glama-status-mcp/0.1"}
)
soup = BeautifulSoup(resp.text, "lxml")

# Find tool names and their containers
print("=== All <p> elements with tool names ===")
for p in soup.find_all("p"):
    txt = p.get_text(strip=True)
    if "_" in txt and len(txt) < 60 and txt.isascii():
        parent_classes = " ".join(p.parent.get("class", [])) if p.parent else ""
        print(f"\n  Tool: '{txt}'")
        print(f"  Parent classes: [{parent_classes[:80]}]")
        # Walk up to find a section-like container
        for ancestor in [p.parent, p.parent.parent, p.parent.parent.parent]:
            if ancestor:
                ac = " ".join(ancestor.get("class", []))
                aname = ancestor.name
                print(f"    ancestor <{aname}> classes: [{ac[:60]}]")
                # Count spans with scores in this ancestor
                spans = ancestor.find_all("span", string=re.compile(r"\d\.\d/5"))
                if spans:
                    for s in spans:
                        print(f"      score: {s.get_text(strip=True)}")
                # Find grade text
                texts = ancestor.find_all(string=re.compile(r"^[ABCDF]$"))
                for t in texts:
                    print(f"      grade: {t.strip()}")
                # Find dimension scores
                for dim_label in ["Purpose", "Usage", "Behavior", "Parameters", "Conciseness", "Completeness"]:
                    dim_el = ancestor.find(string=re.compile(dim_label))
                    if dim_el:
                        dim_parent = dim_el.parent
                        dim_text = dim_parent.get_text(strip=True) if dim_parent else dim_el
                        print(f"      dim {dim_label}: {dim_text[:80]}")
        break  # Just first one for debugging

# Check the coherence section
print("\n=== Coherence section ===")
for text in ["Server Coherence", "Disambiguation", "Naming", "Tool Count"]:
    found = soup.find_all(string=re.compile(text))
    for f in found[:2]:
        p = f.parent
        classes = " ".join(p.get("class", []))
        print(f"  '{text}' in <{p.name} class='{classes[:50]}'>: parent text={p.parent.get_text(strip=True)[:120] if p.parent else ''}")

# Check the lowest score mention  
print("\n=== Lowest score context ===")
low = soup.find(string=re.compile(r"Lowest: 2.4"))
if low:
    for anc in [low.parent, low.parent.parent]:
        if anc:
            print(f"  <{anc.name}> {anc.get_text(strip=True)[:200]}")
