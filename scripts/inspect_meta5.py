"""Full raw HTML dump around key areas."""
import httpx
import re
from bs4 import BeautifulSoup

resp = httpx.get(
    "https://glama.ai/mcp/servers/sandraschi/virtualization-mcp/score",
    follow_redirects=True, timeout=30,
    headers={"User-Agent": "glama-status-mcp/0.1"}
)
soup = BeautifulSoup(resp.text, "lxml")

# Print first 5000 chars of body text
body = resp.text
print("=== Body text around 'Coherence' ===")
idx = body.find("Server Coherence")
if idx >= 0:
    print(body[max(0,idx-200):idx+500])
    
print("\n\n=== Body text around 'Maintenance' ===")
idx = body.find("Maintenance")
if idx >= 0:
    print(body[max(0,idx-200):idx+500])

# Find all <li> elements in the page  
print("\n=== All <li> elements ===")
for li in soup.find_all("li"):
    txt = li.get_text(strip=True)
    if len(txt) > 10 and len(txt) < 200:
        print(f"  <li> class={li.get('class', '')} '{txt[:150]}'")
