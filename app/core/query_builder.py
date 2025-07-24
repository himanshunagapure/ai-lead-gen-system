from typing import List, Optional
import random

TRAVEL_SYNONYMS = [
    "travel", "trip", "tour", "vacation", "holiday", "journey", "excursion", "getaway"
]

TRAVEL_VERTICALS = [
    "hotel", "resort", "hostel", "guesthouse", "restaurant", "cafe", "tour operator", "travel agency", "blogger", "event organizer"
]

NEGATIVE_KEYWORDS = [
    "job", "career", "hiring", "free", "template", "sample"
]

SEARCH_INTENTS = {
    "informational": ["guide", "tips", "review", "blog", "information"],
    "commercial": ["book", "reservation", "deal", "price", "offer"]
}

def build_query(
    base: str,
    vertical: Optional[str] = None,
    location: Optional[str] = None,
    intent: Optional[str] = None,
    synonyms: bool = True,
    exclude: Optional[List[str]] = None
) -> str:
    parts = []
    if synonyms:
        synonym = random.choice(TRAVEL_SYNONYMS)
        parts.append(synonym)
    else:
        parts.append(base)
    if vertical:
        parts.append(vertical)
    if location:
        parts.append(location)
    if intent and intent in SEARCH_INTENTS:
        parts.extend(SEARCH_INTENTS[intent])
    if exclude is None:
        exclude = NEGATIVE_KEYWORDS
    exclude_str = " ".join([f"-{word}" for word in exclude])
    query = " ".join(parts) + " " + exclude_str
    return query.strip() 