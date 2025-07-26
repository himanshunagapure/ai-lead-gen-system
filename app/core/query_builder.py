from typing import List, Optional

def build_query(
    base: Optional[str] = None,
    location: Optional[str] = None,
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    add_travel_keywords: bool = True,
    add_target_groups: bool = True,
    add_trip_types: bool = True,
    extra: Optional[List[str]] = None,
) -> str:
    """
    Build a flexible search query for bus travel agency lead generation.
    - base: main search term (e.g., 'bus travel', 'group tour')
    - location: city, region, or country
    - include: additional keywords to include
    - exclude: negative keywords to exclude
    - add_travel_keywords: include general travel-related terms
    - add_target_groups: include target audience keywords
    - add_trip_types: include trip/journey/holiday/tour/visit synonyms
    - extra: any extra keywords
    """
    parts = []
    if base:
        parts.append(base)
    if location:
        parts.append(location)
    if add_travel_keywords:
        parts.extend([
            "travel", "vacation", "journey", "holiday", "tour", "visit", "trip"
        ])
    if add_target_groups:
        parts.extend([
            "traveler", "adventurer", "tourist", "visitor",
            "company", "corporate", "business", "group",
            "travel influencer", "blogger", "vlogger", "content creator",
            "tour operator", "bus operator", "travel agency",
            "event organizer", "event planner"
        ])
    if add_trip_types:
        parts.extend([
            "planning", "plan a trip", "plan a tour", "plan a holiday", "plan a visit"
        ])
    if include:
        parts.extend(include)
    if extra:
        parts.extend(extra)
    if exclude is None:
        exclude = ["job", "career", "hiring", "free", "template", "sample"]
    exclude_str = " ".join([f"-{word}" for word in exclude])
    query = " ".join(parts) + " " + exclude_str
    return query.strip() 