import re
from typing import Dict, Any, List

TRAVEL_VERTICALS = [
    "hotel", "resort", "hostel", "restaurant", "cafe", "tour operator", "travel agency", "blogger", "event organizer"
]

CONTENT_TYPES = {
    "business": ["hotel", "resort", "restaurant", "agency", "operator", "listing"],
    "blog": ["blog", "post", "story"],
    "review": ["review", "rating", "score"],
    "social": ["facebook", "instagram", "twitter", "linkedin"]
}

COMMERCIAL_KEYWORDS = ["book", "reservation", "deal", "price", "offer", "buy", "sale"]
INFORMATIONAL_KEYWORDS = ["guide", "tips", "review", "blog", "information", "how to"]

SPAM_PATTERNS = [r"free\s+gift", r"click here", r"subscribe now", r"win\s+money"]


def classify_content_type(text: str) -> str:
    text_l = text.lower()
    for ctype, keywords in CONTENT_TYPES.items():
        for kw in keywords:
            if kw in text_l:
                return ctype
    return "other"

def classify_vertical(text: str) -> str:
    text_l = text.lower()
    for v in TRAVEL_VERTICALS:
        if v in text_l:
            return v
    return "other"

def classify_intent(text: str) -> str:
    text_l = text.lower()
    if any(kw in text_l for kw in COMMERCIAL_KEYWORDS):
        return "commercial"
    if any(kw in text_l for kw in INFORMATIONAL_KEYWORDS):
        return "informational"
    return "unknown"

def score_content_quality(text: str) -> float:
    # Simple heuristic: length and keyword presence
    length_score = min(len(text) / 1000, 1.0)
    keyword_score = 0.2 if any(kw in text.lower() for kw in TRAVEL_VERTICALS) else 0.0
    return round(length_score + keyword_score, 2)

def detect_spam(text: str) -> bool:
    for pat in SPAM_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            return True
    return False

def extract_keywords(text: str, top_n: int = 10) -> List[str]:
    words = re.findall(r"\b\w{4,}\b", text.lower())
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in sorted_words[:top_n]]

def classify_content(text: str) -> Dict[str, Any]:
    return {
        "type": classify_content_type(text),
        "vertical": classify_vertical(text),
        "intent": classify_intent(text),
        "quality_score": score_content_quality(text),
        "is_spam": detect_spam(text),
        "keywords": extract_keywords(text),
    } 