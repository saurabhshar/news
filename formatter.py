"""Jinja2-based HTML formatter for the daily newspaper."""

import os
from collections import OrderedDict
from datetime import date
from typing import List

from jinja2 import Environment, FileSystemLoader

from fetcher import NewsItem

# Section display order (General News is always last)
SECTION_ORDER = [
    "Politics & Government",
    "Economy & Business",
    "Society & Immigration",
    "Sports",
    "Education & Science",
    "Culture & Entertainment",
    "Local & Regional",
    "General News",
]


def group_by_section(items: List[NewsItem]) -> OrderedDict:
    """Group items by section in the preferred display order."""
    grouped: OrderedDict = OrderedDict()

    # Initialize all sections in order (including only those with items)
    seen_sections = {item.section for item in items}
    for section in SECTION_ORDER:
        if section in seen_sections:
            grouped[section] = []
    # Any unexpected sections go at the end before General News
    for section in seen_sections:
        if section not in grouped:
            grouped[section] = []

    for item in items:
        grouped[item.section].append(item)

    return grouped


def render(items: List[NewsItem], template_dir: str, output_path: str) -> None:
    """Render the newspaper HTML and write it to output_path."""
    today = date.today().strftime("%B %d, %Y")
    sections = group_by_section(items)
    total_items = len(items)
    source_names = {item.source_name for item in items}

    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=True,
    )
    template = env.get_template("newspaper.html.j2")
    html = template.render(
        date=today,
        sections=sections,
        total_items=total_items,
        source_count=len(source_names),
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
