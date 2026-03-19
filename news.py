#!/usr/bin/env python3
"""Germany Daily — CLI entry point."""

import argparse
import os
import sys
from datetime import date

import yaml

from fetcher import fetch_all_feeds
from formatter import render


def main():
    parser = argparse.ArgumentParser(
        description="Generate today's German-news-in-English newspaper HTML."
    )
    parser.add_argument(
        "--config",
        default=os.path.join(os.path.dirname(__file__), "config.yaml"),
        help="Path to config YAML file (default: config.yaml)",
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join(os.path.dirname(__file__), "output"),
        help="Directory to write the HTML file (default: ./output)",
    )
    args = parser.parse_args()

    # Load config
    config_path = os.path.abspath(args.config)
    if not os.path.exists(config_path):
        print(f"Error: config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Fetch feeds
    print("Fetching RSS feeds...")
    items = fetch_all_feeds(config)
    print(f"  Total items after deduplication and capping: {len(items)}")

    if not items:
        print("Warning: no items fetched. Check your network connection or feed URLs.")
        sys.exit(1)

    # Render HTML
    today_str = date.today().strftime("%Y-%m-%d")
    output_path = os.path.join(os.path.abspath(args.output_dir), f"{today_str}.html")
    template_dir = os.path.join(os.path.dirname(__file__), "templates")

    print(f"Rendering newspaper -> {output_path}")
    render(items, template_dir, output_path)
    print("Done! Open the file in your browser to read today's news.")


if __name__ == "__main__":
    main()
