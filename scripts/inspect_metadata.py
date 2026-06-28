"""Debug metadata parsing: coherence, TDQS, maintenance."""
import httpx
import re
from bs4 import BeautifulSoup

resp = httpx.get(
    "https://glama.ai/mcp/servers/sandraschi/virtualization-mcp/score",
    follow_redirects=True, timeout=30,
    headers={"User-Agent": "glama-status-mcp/0.1"}
)
soup = BeautifulSoup(resp.text, "lxml")

# 1. Coherence sub-scores
print("=== Coherence sub-scores ===")
for label in ["Disambiguation", "Naming Consistency", "Tool Count", "Completeness"]:
    el = soup.find(string=re.compile(f"^{re.escape(label)}$"))
    if el:
        print(f"  Found '{label}'")
        print(f"    tag: <{el.parent.name}> class={el.parent.get('class', '')}")
        print(f"    text: '{el.strip()}'")
        container = el.parent
        if container:
            txt = container.get_text(strip=True)
            print(f"    container text: '{txt}'")
            val = re.search(r'([\d.]+)\s*/\s*5', txt)
            if val:
                print(f"    PARSED score: {val.group(1)}")
            else:
                print(f"    NO SCORE MATCH in container text")
                # Try looking for sibling
                parent_div = container.parent
                siblings = parent_div.find_all(recursive=False)
                print(f"    parent siblings: {[s.name + ' class=' + str(s.get('class',''))[:40] for s in siblings]}")
                # Look for any span with score
                for span in parent_div.find_all("span"):
                    st = span.get_text(strip=True)
                    if re.search(r'\d/\d', st):
                        print(f"    found score span: '{st}'")
    else:
        print(f"  NOT FOUND: '{label}'")

# 2. TDQS
print("\n=== TDQS ===")
for tag in soup.find_all(["p", "div", "span"]):
    txt = tag.get_text(strip=True)
    if "Average" in txt and "Lowest" in txt:
        print(f"  Found TDQS text in <{tag.name}> class={tag.get('class', '')}")
        print(f"  text: '{txt}'")
        m_mean = re.search(r'Average([\d.]+)/5', txt)
        m_min = re.search(r'Lowest:\s*([\d.]+)/5', txt)
        if m_mean: print(f"  PARSED mean: {m_mean.group(1)}")
        else: print(f"  NO MEAN MATCH (pattern: Average([0-9.]+)/5)")
        if m_min: print(f"  PARSED min: {m_min.group(1)}")
        else: print(f"  NO MIN MATCH")

# 3. Maintenance
print("\n=== Maintenance ===")
for span in soup.find_all("span"):
    txt = span.get_text(strip=True)
    if txt == "Maintenance":
        print(f"  Found Maintenance span")
        print(f"    class={span.get('class', '')}")
        parent = span.parent
        print(f"    parent: <{parent.name}> class={parent.get('class', '')}")
        print(f"    parent text: '{parent.get_text(strip=True)[:100]}'")
        # Check for grade letter
        grade = re.search(r'\b[ABCDF]\b', parent.get_text(strip=True))
        if grade:
            print(f"    PARSED grade: {grade.group(0)}")
        else:
            print(f"    NO GRADE in parent text")
            # Walk up
            for ancestor in [parent.parent, parent.parent.parent]:
                if ancestor:
                    atxt = ancestor.get_text(strip=True)
                    grade2 = re.search(r'\b[ABCDF]\b', atxt)
                    if grade2:
                        print(f"    found grade '{grade2.group(0)}' in <{ancestor.name}>")
                        break

# 4. Coherence grade letter
print("\n=== Coherence Grade ===")
for span in soup.find_all("span"):
    txt = span.get_text(strip=True)
    if txt == "Server Coherence":
        section = span.find_parent(["div", "section"])
        if section:
            stxt = section.get_text(strip=True)
            grade = re.search(r'\b[ABCDF]\b', stxt)
            if grade:
                print(f"  Coherence grade: {grade.group(0)} in parent text")
            else:
                # Try looking at siblings
                ns = span.find_next_sibling()
                if ns:
                    print(f"  next sibling: <{ns.name}> text='{ns.get_text(strip=True)[:30]}'")
                parent = span.parent
                ptext = parent.get_text(strip=True)
                grade2 = re.search(r'\b([ABCDF])\b', ptext)
                if grade2:
                    print(f"  Grade '{grade2.group(0)}' in parent text: '{ptext[:80]}'")
