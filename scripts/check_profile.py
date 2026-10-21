#!/usr/bin/env python3
"""Offline validation for profile README and first-party SVG assets.

Designed to run both locally and in GitHub Actions without dependencies.
This verifies source integrity; browser-specific layout still requires a visual
review in GitHub's light and dark themes.
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
REQUIRED = {
    "assets/profile-dark.svg",
    "assets/profile-light.svg",
    "assets/nfl-dark.svg",
    "assets/nfl-light.svg",
    "assets/nba-dark.svg",
    "assets/nba-light.svg",
    "assets/gridiron-dark.svg",
    "assets/gridiron-light.svg",
    "assets/activity-dark.svg",
    "assets/activity-light.svg",
}
REPOS = (
    "fantasy_football_dashboard",
    "nfl_weekly_simulation",
    "nba_daily_simulation",
    "shiny_predictive_football_app",
    "gmat_quant_pwa",
)


class AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.images: list[dict[str, str]] = []
        self.sources: list[dict[str, str]] = []
        self.links: list[str] = []
        self.details = 0
        self.pictures = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        d = {key: value or "" for key, value in attrs}
        if tag == "img":
            self.images.append(d)
        if tag == "source":
            self.sources.append(d)
        if tag == "a" and "href" in d:
            self.links.append(d["href"])
        if tag == "details":
            self.details += 1
        if tag == "picture":
            self.pictures += 1


def main() -> int:
    errors = []
    body = README.read_text(encoding="utf-8")
    if len(body.encode("utf-8")) >= 500 * 1024:
        errors.append("README exceeds GitHub's 500 KiB rendered-readme truncation limit")
    if "## How I work" in body:
        errors.append("The obsolete generic 'How I work' block has returned")
    if any(s in body.lower() for s in ("<iframe", "<script", "javascript:")):
        errors.append("README includes active HTML/JavaScript unsupported by GitHub")
    if "<table>" in body:
        errors.append("Fixed-width HTML table found: use responsive Markdown blocks instead")
    if body.count("<details>") != body.count("</details>"):
        errors.append("Unbalanced interactive details blocks")
    if body.count("<picture>") != body.count("</picture>"):
        errors.append("Unbalanced theme image blocks")

    parsed = AssetParser()
    parsed.feed(body)
    for image in parsed.images:
        if not image.get("alt", "").strip():
            errors.append(f"Missing image description for {image.get('src', '')}")
    relative = set()
    for source in parsed.images + parsed.sources:
        for attr in ("src", "srcset"):
            value = source.get(attr, "").strip()
            if value.startswith("./"):
                relative.add(value[2:])
    for path in sorted(REQUIRED | relative):
        real = ROOT / path
        if not real.is_file():
            errors.append(f"Missing relative asset: {path}")
        elif real.suffix == ".svg":
            try:
                ET.parse(real)
            except ET.ParseError as error:
                errors.append(f"Invalid SVG XML {path}: {error}")
    for repo in REPOS:
        if f"https://github.com/jviola1019/{repo}" not in body:
            errors.append(f"Missing canonical repository link: {repo}")
    for heading in ("## Selected work", "## Research notes", "## Project pulse"):
        if heading not in body:
            errors.append(f"Missing primary section {heading}")
    for anchor in ("#selected-work", "#research-notes", "#project-pulse"):
        if anchor not in body:
            errors.append(f"Missing page navigation anchor {anchor}")
    for name in ("profile", "nfl", "nba", "gridiron", "activity"):
        if f"{name}-dark.svg" not in body or f"{name}-light.svg" not in body:
            errors.append(f"Missing dark/light variant for {name}")
    if errors:
        print("\n".join(f"FAIL: {item}" for item in errors), file=sys.stderr)
        return 1
    print(
        f"PASS: README {len(body.encode('utf-8'))} bytes, "
        f"{len(parsed.images)} described images, {parsed.pictures} themed visuals, "
        f"{parsed.details} native expandable sections, "
        f"{len(relative)} referenced local assets, {len(REPOS)} featured repos."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
