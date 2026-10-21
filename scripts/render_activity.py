#!/usr/bin/env python3
"""Render a source-backed activity graphic for the public profile README.

No invented performance metrics or external dependencies. The SVG changes only
when the latest commit in one of the explicitly selected public repositories
changes. A failed API read fails the workflow without overwriting existing art.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

OWNER = "jviola1019"
REPOSITORIES = (
    ("RAE / Roster Analytics Engine", "fantasy_football_dashboard"),
    ("NFL / Game Simulation", "nfl_weekly_simulation"),
    ("NBA / Daily Simulation", "nba_daily_simulation"),
    ("Gridiron DNA Lab", "shiny_predictive_football_app"),
    ("GMAT Study PWA", "gmat_quant_pwa"),
)
ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"


def get_latest(label: str, slug: str) -> dict[str, str]:
    url = f"https://api.github.com/repos/{OWNER}/{slug}/commits?per_page=1"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "jviola1019-profile-readme-activity",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=15) as response:
        commits = json.load(response)
    if not isinstance(commits, list) or not commits:
        raise ValueError(f"No recent commit available for {slug}")
    commit = commits[0]
    sha = commit["sha"][:7]
    raw_date = commit["commit"]["committer"]["date"]
    date = dt.datetime.fromisoformat(raw_date.replace("Z", "+00:00")).strftime("%b %d, %Y")
    return {"label": label, "slug": slug, "sha": sha, "date": date}


def render(items: list[dict[str, str]], theme: str) -> str:
    dark = theme == "dark"
    bg = "#0e1a2b" if dark else "#f7fafc"
    panel = "#142337" if dark else "#ffffff"
    text = "#eef6fc" if dark else "#193044"
    muted = "#bdccda" if dark else "#455b6d"
    rule = "#395066" if dark else "#ccd9e0"
    accent = "#78e4d2" if dark else "#006e72"
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="431" viewBox="0 0 900 431" role="img" aria-labelledby="t d">',
        '<title id="t">Recent public repository activity</title>',
        '<desc id="d">Latest main-branch commits of five public portfolio repositories, refreshed by a GitHub Actions workflow.</desc>',
        f'<rect width="900" height="431" rx="15" fill="{bg}"/>',
        f'<rect x="1" y="1" width="898" height="429" rx="14" stroke="{rule}" fill="none"/>',
        f'<text x="32" y="50" font-family="Arial,Helvetica,sans-serif" font-size="26" font-weight="700" fill="{text}">PUBLIC PROJECT ACTIVITY</text>',
        f'<text x="32" y="76" font-family="Arial,Helvetica,sans-serif" font-size="14" fill="{muted}">Latest commits · GitHub source · not model performance</text>',
    ]
    for index, item in enumerate(items):
        y = 100 + index * 59
        label = html.escape(item["label"], quote=True)
        date = html.escape(item["date"], quote=True)
        sha = html.escape(item["sha"], quote=True)
        parts += [
            f'<rect x="27" y="{y}" width="846" height="54" rx="8" fill="{panel}"/>',
            f'<rect x="40" y="{y + 18}" width="6" height="18" rx="2" fill="{accent}"/>',
            f'<text x="60" y="{y + 32}" font-family="Arial,Helvetica,sans-serif" font-size="18" font-weight="700" fill="{text}">{label}</text>',
            f'<text x="848" y="{y + 31}" text-anchor="end" font-family="Arial,Helvetica,sans-serif" font-size="15" fill="{muted}">{date} · {sha}</text>',
        ]
    parts += [
        f'<text x="30" y="412" font-family="Arial,Helvetica,sans-serif" font-size="12" fill="{muted}">Automated via GitHub Actions; dates reflect source commits, not activity on this profile.</text>',
        '</svg>',
    ]
    return "\n".join(parts) + "\n"


def main() -> None:
    items = [get_latest(label, slug) for label, slug in REPOSITORIES]
    ASSETS.mkdir(parents=True, exist_ok=True)
    for theme in ("dark", "light"):
        path = ASSETS / f"activity-{theme}.svg"
        content = render(items, theme)
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            path.write_text(content, encoding="utf-8")
    print(json.dumps(items, indent=2))


if __name__ == "__main__":
    main()
