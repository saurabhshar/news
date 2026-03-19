"""RSS feed fetcher, parser, and categorizer."""

import re
import html
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Dict, Any

import feedparser
from dateutil import parser as dateutil_parser


@dataclass
class NewsItem:
    title: str
    description: str    # RSS summary field, HTML-stripped
    link: str           # Original article URL for attribution
    pub_date: datetime
    source_name: str    # Human-readable feed name
    section: str        # Assigned newspaper section
    germany_priority: bool = False


def strip_html(text: str) -> str:
    """Remove HTML tags and decode HTML entities."""
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Decode HTML entities
    text = html.unescape(text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_date(entry: Any) -> datetime:
    """Extract and parse publication date from a feedparser entry."""
    # Try published_parsed (struct_time) first
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        except Exception:
            pass
    # Try updated_parsed
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        try:
            return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
        except Exception:
            pass
    # Try string-based parsing
    for field in ("published", "updated", "created"):
        value = getattr(entry, field, None)
        if value:
            try:
                return dateutil_parser.parse(value)
            except Exception:
                pass
    # Fallback to now
    return datetime.now(timezone.utc)


def assign_section(item_text: str, sections: List[Dict]) -> str:
    """Score item against each section's keywords and return the best match."""
    text_lower = item_text.lower()
    best_section = "General News"
    best_score = 0

    for section in sections:
        score = 0
        for keyword in section["keywords"]:
            if keyword.lower() in text_lower:
                score += 1
        if score > best_score:
            best_score = score
            best_section = section["name"]

    return best_section


def fetch_all_feeds(config: Dict) -> List[NewsItem]:
    """Fetch all RSS feeds and return a deduplicated, sorted list of NewsItems."""
    feeds = config.get("feeds", [])
    sections = config.get("sections", [])
    max_per_section = config.get("max_items_per_section", 5)

    all_items: List[NewsItem] = []
    seen_links: set = set()
    seen_titles: set = set()

    for feed_cfg in feeds:
        name = feed_cfg["name"]
        url = feed_cfg["url"]
        is_germany = feed_cfg.get("germany_priority", False)
        print(f"  Fetching: {name} ...", end=" ", flush=True)
        try:
            parsed = feedparser.parse(url)
            entries = parsed.get("entries", [])
            count = 0
            for entry in entries:
                link = getattr(entry, "link", "") or ""
                if not link or link in seen_links:
                    continue

                raw_title = strip_html(getattr(entry, "title", "") or "")
                normalized_title = re.sub(r"[^a-z0-9]", "", raw_title.lower())
                if normalized_title and normalized_title in seen_titles:
                    continue

                seen_links.add(link)
                seen_titles.add(normalized_title)

                title = raw_title
                description = strip_html(
                    getattr(entry, "summary", "")
                    or getattr(entry, "description", "")
                    or ""
                )
                pub_date = parse_date(entry)
                combined_text = f"{title} {description}"
                section = assign_section(combined_text, sections)

                all_items.append(NewsItem(
                    title=title,
                    description=description,
                    link=link,
                    pub_date=pub_date,
                    source_name=name,
                    section=section,
                    germany_priority=is_germany,
                ))
                count += 1
            print(f"{count} items")
        except Exception as e:
            print(f"ERROR: {e}")

    # Sort: Germany-priority first, then by pub_date descending
    all_items.sort(key=lambda x: (not x.germany_priority, x.pub_date.timestamp() * -1))

    # Cap per section
    section_counts: Dict[str, int] = {}
    capped: List[NewsItem] = []
    for item in all_items:
        sec = item.section
        if section_counts.get(sec, 0) < max_per_section:
            capped.append(item)
            section_counts[sec] = section_counts.get(sec, 0) + 1

    return capped
