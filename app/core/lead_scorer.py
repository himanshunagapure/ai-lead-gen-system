import re
from datetime import datetime
from typing import Dict, Any, Optional

TRAVEL_KEYWORDS = [
    "hotel", "resort", "hostel", "restaurant", "tour", "travel", "agency", "blogger", "event", "operator"
]

# Completeness scoring

def completeness_score(lead: Dict[str, Any]) -> float:
    score = 0.0
    fields = [
        ('business_name', 0.2),
        ('email', 0.2),
        ('phone', 0.15),
        ('website', 0.15),
        ('address', 0.1),
        ('contact_person', 0.1),
        ('lead_type', 0.1)
    ]
    for field, weight in fields:
        if lead.get(field):
            score += weight
    return round(score, 2)

# Relevance scoring

def relevance_score(lead: Dict[str, Any], target_keywords: Optional[list] = None, target_geo: Optional[str] = None) -> float:
    score = 0.0
    keywords = target_keywords or TRAVEL_KEYWORDS
    text = " ".join(str(lead.get(f, "")).lower() for f in ["business_name", "lead_type", "description", "website"])
    if any(kw in text for kw in keywords):
        score += 0.5
    if target_geo and target_geo.lower() in text:
        score += 0.2
    if lead.get("website"):
        score += 0.1
    if lead.get("social_profiles"):
        score += 0.1
    if lead.get("review_count", 0) > 0:
        score += 0.1
    return round(min(score, 1.0), 2)

# Freshness & activity scoring

def freshness_score(lead: Dict[str, Any], now: Optional[datetime] = None) -> float:
    score = 0.0
    now = now or datetime.utcnow()
    # Content publication date
    pub_date = lead.get("publish_date") or lead.get("content_date")
    if pub_date:
        try:
            dt = datetime.fromisoformat(pub_date)
            days = (now - dt).days
            if days < 30:
                score += 0.5
            elif days < 180:
                score += 0.3
            elif days < 365:
                score += 0.1
        except Exception:
            pass
    # Website last updated
    last_updated = lead.get("website_last_updated")
    if last_updated:
        try:
            dt = datetime.fromisoformat(last_updated)
            days = (now - dt).days
            if days < 30:
                score += 0.3
            elif days < 180:
                score += 0.2
            elif days < 365:
                score += 0.1
        except Exception:
            pass
    # Social activity (recent post)
    if lead.get("recent_social_activity_date"):
        try:
            dt = datetime.fromisoformat(lead["recent_social_activity_date"])
            days = (now - dt).days
            if days < 30:
                score += 0.2
            elif days < 180:
                score += 0.1
        except Exception:
            pass
    # Review recency
    if lead.get("recent_review_date"):
        try:
            dt = datetime.fromisoformat(lead["recent_review_date"])
            days = (now - dt).days
            if days < 30:
                score += 0.1
        except Exception:
            pass
    # Domain age (older = more trusted)
    if lead.get("domain_age_years"):
        try:
            years = float(lead["domain_age_years"])
            if years > 5:
                score += 0.1
        except Exception:
            pass
    return round(min(score, 1.0), 2)

# Final scoring

def score_lead(lead: Dict[str, Any], target_keywords: Optional[list] = None, target_geo: Optional[str] = None, now: Optional[datetime] = None) -> Dict[str, Any]:
    comp = completeness_score(lead)
    rel = relevance_score(lead, target_keywords, target_geo)
    fresh = freshness_score(lead, now)
    final = round(0.4 * comp + 0.4 * rel + 0.2 * fresh, 2)
    return {
        "completeness_score": comp,
        "relevance_score": rel,
        "freshness_score": fresh,
        "final_score": final,
        "scoring_factors": {
            "completeness": comp,
            "relevance": rel,
            "freshness": fresh
        },
        "scored_at": (now or datetime.utcnow()).isoformat()
    } 