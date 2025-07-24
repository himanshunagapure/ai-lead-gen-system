import re
from newspaper import Article
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
import json
import requests

def extract_article_content(url: str, html: Optional[str] = None) -> Dict[str, Any]:
    article = Article(url)
    if html:
        article.set_html(html)
    article.download_state = 2  # STATE_SUCCESS
    try:
        article.parse()
    except Exception:
        return {}
    return {
        "title": article.title,
        "authors": article.authors,
        "publish_date": article.publish_date,
        "text": article.text,
        "top_image": article.top_image,
        "movies": article.movies,
    }

def extract_emails(text: str) -> List[str]:
    # Standard email
    emails = set(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text))
    # Obfuscated emails (e.g., info [at] example [dot] com)
    obfuscated = re.findall(r"([a-zA-Z0-9_.+-]+)\s*\[at\]\s*([a-zA-Z0-9-]+)\s*\[dot\]\s*([a-zA-Z0-9-.]+)", text, re.IGNORECASE)
    for parts in obfuscated:
        emails.add(f"{parts[0]}@{parts[1]}.{parts[2]}")
    return list(emails)

def extract_phones(text: str) -> List[str]:
    # Standard phone numbers
    phones = set(re.findall(r"\+?\d[\d\s().-]{7,}\d", text))
    # Obfuscated phones (e.g., +91 [space] 12345 [space] 67890)
    obfuscated = re.findall(r"\+?\d{1,3}\s*\[space\]\s*\d{3,5}\s*\[space\]\s*\d{3,5}", text)
    for phone in obfuscated:
        phones.add(phone.replace("[space]", " ").replace(" ", ""))
    return list(phones)

def extract_social_links(html: str) -> List[str]:
    soup = BeautifulSoup(html, "lxml")
    social_domains = [
        "facebook.com", "instagram.com", "twitter.com", "linkedin.com",
        "youtube.com", "t.me", "telegram.me", "wa.me", "whatsapp.com"
    ]
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if any(domain in href for domain in social_domains):
            links.append(href)
    return list(set(links))

def extract_contact_page_links(html: str, base_url: str = "") -> List[str]:
    soup = BeautifulSoup(html, "lxml")
    contact_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        text = a.get_text().lower()
        if "contact" in href or "contact" in text:
            link = href
            if base_url and not link.startswith("http") and not link.startswith("/"):
                link = base_url.rstrip("/") + "/" + link.lstrip("/")
            contact_links.append(link)
    return list(set(contact_links))

def extract_physical_addresses(html: str) -> List[str]:
    # Try to extract schema.org address
    addresses = []
    soup = BeautifulSoup(html, "lxml")
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                if data.get("@type") in ["Organization", "LocalBusiness", "Place", "Hotel"] and "address" in data:
                    addr = data["address"]
                    if isinstance(addr, dict):
                        address_str = ", ".join([str(addr.get(k, "")) for k in ["streetAddress", "addressLocality", "addressRegion", "postalCode", "addressCountry"] if addr.get(k)])
                        if address_str:
                            addresses.append(address_str)
                    elif isinstance(addr, str):
                        addresses.append(addr)
        except Exception:
            continue
    # Fallback: regex for addresses (very basic, US/India style)
    regex = r"\d{1,5} [\w .,-]+,? [\w .,-]+,? [A-Z]{2,} ?\d{3,6}"
    addresses += re.findall(regex, html)
    return list(set(addresses))

def extract_organization_name(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "lxml")
    # Try schema.org
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                if data.get("@type") in ["Organization", "LocalBusiness", "Place", "Hotel"] and "name" in data:
                    return data["name"]
        except Exception:
            continue
    # Fallback: title tag
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    # Fallback: meta og:site_name
    meta = soup.find("meta", property="og:site_name")
    if meta and meta.get("content"):
        return meta["content"].strip()
    return None

def extract_job_titles(text: str) -> List[str]:
    # Simple regex for common job titles
    titles = re.findall(r"\b(CEO|Founder|Owner|Manager|Director|President|Principal|Partner|Head|Lead|Chairman|Chief [A-Za-z ]+|[A-Za-z]+ Officer)\b", text, re.IGNORECASE)
    return list(set([t.strip() for t in titles]))

def fetch_and_extract_contact_info(base_url: str, contact_links: List[str]) -> Dict[str, List[str]]:
    emails = set()
    phones = set()
    for link in contact_links:
        # Normalize link
        if link.startswith("/"):
            url = base_url.rstrip("/") + link
        elif link.startswith("http"):
            url = link
        else:
            url = base_url.rstrip("/") + "/" + link.lstrip("/")
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                html = resp.text
                emails.update(extract_emails(html))
                phones.update(extract_phones(html))
        except Exception:
            continue
    return {"emails": list(emails), "phones": list(phones)} 