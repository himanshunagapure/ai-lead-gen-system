import re
import nltk
from bs4 import BeautifulSoup
from typing import Optional

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')
from nltk.corpus import stopwords
from nltk import word_tokenize

EN_STOPWORDS = set(stopwords.words('english'))

def clean_html(raw_html: str) -> str:
    # Remove HTML tags and JavaScript
    soup = BeautifulSoup(raw_html, "lxml")
    for tag in soup(["script", "style", "noscript", "iframe"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return text

def clean_whitespace(text: str) -> str:
    # Remove excessive whitespace and special characters
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    return text.strip()

def detect_language(text: str) -> Optional[str]:
    # Simple language detection using stopwords
    tokens = set(word_tokenize(text.lower()))
    if len(tokens & EN_STOPWORDS) > 3:
        return "en"
    return None

def normalize_encoding(text: str) -> str:
    # Normalize text encoding to UTF-8
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="ignore")
    return text

def remove_boilerplate(text: str) -> str:
    # Remove common boilerplate (headers, footers) only if the whole line matches
    boilerplate_patterns = [
        r"^copyright$",
        r"^all rights reserved$",
        r"^privacy policy$",
        r"^terms of service$",
        r"^footer$",
        r"^header$"
    ]
    lines = text.splitlines()
    cleaned_lines = []
    for l in lines:
        if not any(re.search(pat, l.strip(), re.I) for pat in boilerplate_patterns):
            cleaned_lines.append(l)
    return " ".join(cleaned_lines)

def extract_main_content(text: str) -> str:
    # Heuristic: return the largest paragraph or block
    blocks = re.split(r"\n{2,}", text)
    if not blocks:
        return text
    return max(blocks, key=len)

def process_text_pipeline(raw_html: str) -> dict:
    text = clean_html(raw_html)
    text = clean_whitespace(text)
    text = remove_boilerplate(text)
    main_content = extract_main_content(text)
    lang = detect_language(main_content)
    main_content = normalize_encoding(main_content)
    return {
        "clean_text": main_content,
        "language": lang or "unknown"
    } 