#!/usr/bin/env python3
"""Render provenance-backed activity from the curated public project manifest.

The chart shows the most recent default-branch commits among specifically
selected public repositories. A failed API read aborts before any files change.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import os
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "projects.json"
ASSETS = ROOT / "assets"
OWNER = "jviola1019"
FONT = "IBM Plex Sans,Segoe UI,Arial,sans-serif"
MONO = "IBM Plex Mono,Consolas,monospace"


def load_manifest() -> tuple[list[tuple[str, str]], int]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("owner") != OWNER:
        raise ValueError("Unexpected owner in public activity manifest")
    limit = data.get("activity_limit")
    if not isinstance(limit, int) or not 1 <= limit <= 8:
        raise ValueError("activity_limit must be between 1 and 8")
    tracked = []
    seen = set()
    for project in data["projects"]:
        slug = project["slug"]
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", slug) or slug in seen:
            raise ValueError("Invalid or repeated project slug")
        seen.add(slug)
        if project.get("activity"):
            tracked.append((project["label"], slug))
    if len(tracked) < limit:
        raise ValueError("Not enough curated projects to populate activity chart")
    return tracked, limit


def get_latest(label: str, slug: str) -> dict[str, str]:
    request = urllib.request.Request(
        f"https://api.github.com/repos/{OWNER}/{slug}/commits?per_page=1",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "jviola1019-portfolio-activity",
            "X-GitHub-Api-Version": "2022-11-28",
            **({"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"}
               if os.environ.get("GITHUB_TOKEN") else {}),
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        commits = json.load(response)
    if not isinstance(commits, list) or not commits:
        raise ValueError(f"No accessible default-branch commit for {slug}")
    commit = commits[0]
    timestamp = dt.datetime.fromisoformat(commit["commit"]["committer"]["date"].replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        raise ValueError(f"Timezone missing for {slug}")
    return {
        "slug": slug,
        "label": label,
        "date": timestamp.strftime("%b %d, %Y"),
        "sha": commit["sha"][:7],
        "committed_at": timestamp.isoformat(),
    }


def newest_first(items: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(items, key=lambda item: (
        -dt.datetime.fromisoformat(item["committed_at"].replace("Z", "+00:00")).timestamp(),
        item["slug"],
    ))


def render(items: list[dict[str, str]], theme: str) -> str:
    return _render(items, theme, mobile=False)


def render_mobile(items: list[dict[str, str]], theme: str) -> str:
    return _render(items, theme, mobile=True)


def _render(items: list[dict[str, str]], theme: str, mobile: bool) -> str:
    if theme not in ("dark", "light"):
        raise ValueError("Unrecognized theme")
    items = newest_first(items)
    dark = theme == "dark"
    bg = "#0D151C" if dark else "#F5F4F0"
    card = "#18262E" if dark else "#FFFFFF"
    ink = "#F2F4F1" if dark else "#182831"
    muted = "#B6C2C5" if dark else "#52646B"
    rule = "#35444B" if dark else "#CFD7D6"
    accent = "#E8B576" if dark else "#865D29"
    width = 480 if mobile else 1200
    top = 109 if mobile else 105
    row_height = 91 if mobile else 59
    height = top + len(items) * row_height + 44
    head = "RECENT SOURCE ACTIVITY" if mobile else "SELECTED PROJECT ACTIVITY"
    sub = "LATEST DEFAULT-BRANCH COMMITS / NEWEST FIRST"
    txtsize = 21 if mobile else 21
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="t d">',
        '<title id="t">Selected public project activity</title>',
        f'<desc id="d">{len(items)} curated public projects ordered by newest default-branch commit. Dates and hashes are source metadata; no model-performance claim.</desc>',
        f'<rect width="{width}" height="{height}" rx="7" fill="{bg}"/>',
        f'<rect x="14" y="14" width="{width-28}" height="{height-28}" rx="4" stroke="{rule}" fill="none"/>',
        f'<rect x="32" y="39" width="7" height="7" fill="{accent}"/>',
        f'<text x="50" y="49" font-family="{MONO}" font-size="{15 if mobile else 18}" letter-spacing="1.1" font-weight="600" fill="{ink}">{head}</text>',
        f'<text x="32" y="76" font-family="{MONO}" font-size="{11 if mobile else 13}" fill="{muted}">{sub}</text>',
    ]
    for i, item in enumerate(items):
        y = top + i * row_height
        label = html.escape(item["label"], quote=True)
        date = html.escape(item["date"], quote=True)
        sha = html.escape(item["sha"], quote=True)
        attrslug = html.escape(item["slug"], quote=True)
        attrdate = html.escape(item["committed_at"], quote=True)
        boxw = width - 64
        boxh = 81 if mobile else 50
        parts.extend([
            f'<g data-repository="{attrslug}" data-committed-at="{attrdate}">',
            f'<rect x="32" y="{y}" width="{boxw}" height="{boxh}" rx="4" fill="{card}" stroke="{rule}" stroke-width=".8"/>',
            f'<rect x="43" y="{y+13}" width="4" height="{boxh-26}" fill="{accent}"/>',
            f'<text x="60" y="{y+(31 if mobile else 31)}" font-family="{FONT}" font-size="{txtsize}" font-weight="600" fill="{ink}">{label}</text>',
        ])
        if mobile:
            parts.append(f'<text x="60" y="{y+61}" font-family="{MONO}" font-size="15" fill="{muted}">{date}  /  {sha}</text>')
        else:
            parts.append(f'<text x="{width-52}" y="{y+31}" text-anchor="end" font-family="{MONO}" font-size="16" fill="{muted}">{date}  /  {sha}</text>')
        parts.append('</g>')
    parts.append(f'<text x="32" y="{height-21}" font-family="{MONO}" font-size="{11 if mobile else 13}" fill="{muted}">PUBLIC GITHUB SOURCE / CURATED SELECTION / NO FORECAST METRICS</text>')
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def main() -> None:
    tracked, limit = load_manifest()
    # Fetch all sources before touching any file; prevent silent partial updates.
    items = newest_first([get_latest(label, slug) for label, slug in tracked])[:limit]
    rendered = {
        ASSETS / f"activity-{prefix}{theme}.svg": (
            render_mobile(items, theme) if prefix else render(items, theme)
        )
        for theme in ("dark", "light")
        for prefix in ("", "mobile-")
    }
    ASSETS.mkdir(parents=True, exist_ok=True)
    for path, content in rendered.items():
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            path.write_text(content, encoding="utf-8")
    print(json.dumps(items, indent=2))


if __name__ == "__main__":
    main()
