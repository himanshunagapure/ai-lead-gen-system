from bs4 import BeautifulSoup
import re
import json
from typing import Dict, Any, Optional, List

def parse_html_content(html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    # Remove navigation, ads, and scripts
    for tag in soup(["nav", "header", "footer", "aside", "script", "style", "noscript", "iframe", "form", "ads", "svg"]):
        tag.decompose()
    # Extract main content area (heuristic: largest <div> or <main>)
    main_content = soup.find("main")
    if not main_content:
        divs = soup.find_all("div")
        if divs:
            main_content = max(divs, key=lambda d: len(d.get_text(strip=True)))
        else:
            main_content = soup.body or soup
    text = main_content.get_text(separator=" ", strip=True) if main_content else soup.get_text(separator=" ", strip=True)
    # Extract meta tags
    meta = {m.get("name", m.get("property", "")).lower(): m.get("content", "") for m in soup.find_all("meta") if m.get("content")}
    # Extract structured data (JSON-LD)
    jsonld = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            jsonld.append(json.loads(script.string))
        except Exception:
            continue
    # Extract microdata (simple)
    microdata = []
    for tag in soup.find_all(attrs={"itemtype": True}):
        microdata.append({"itemtype": tag["itemtype"], "properties": tag.attrs})
    # Robust title extraction
    title = ""
    if soup.title and soup.title.string and soup.title.string.strip():
        title = soup.title.string.strip()
    elif soup.find("meta", property="og:title") and soup.find("meta", property="og:title").get("content"):
        title = soup.find("meta", property="og:title")["content"].strip()
    elif soup.find("meta", attrs={"name": "title"}) and soup.find("meta", attrs={"name": "title"}).get("content"):
        title = soup.find("meta", attrs={"name": "title"})["content"].strip()
    elif soup.find("h1") and soup.find("h1").get_text(strip=True):
        title = soup.find("h1").get_text(strip=True)
    return {
        "text": text,
        "meta": meta,
        "jsonld": jsonld,
        "microdata": microdata,
        "title": title,
        "language": soup.html.get("lang") if soup.html else None,
    } 