#!/usr/bin/env python3
"""Offline structural, privacy and provenance checks for the profile portfolio."""
from __future__ import annotations

import datetime as dt
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
MANIFEST = ROOT / "data" / "projects.json"


class AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.images = []
        self.sources = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == "img":
            self.images.append(data)
        elif tag == "source":
            self.sources.append(data)


def main() -> int:
    errors = []
    body = README.read_text(encoding="utf-8")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    projects = data["projects"]
    if data.get("owner") != "jviola1019":
        errors.append("Unexpected project manifest owner")
    if len(body.encode("utf-8")) >= 500 * 1024:
        errors.append("README exceeds the 500 KiB limit")
    for banned in ("<script", "<iframe", "javascript:", "prediction-market-quant", "gmat_quant_pwa"):
        if banned in body.lower():
            errors.append(f"Unsafe, private or unavailable reference: {banned}")
    if body.count("<picture>") != body.count("</picture>"):
        errors.append("Unbalanced picture elements")
    if body.count("<details>") != body.count("</details>"):
        errors.append("Unbalanced details elements")
    parsed = AssetParser()
    parsed.feed(body)
    if not parsed.images or not parsed.sources:
        errors.append("Missing accessible images or dark/light sources")
    relative = set()
    for image in parsed.images:
        if not (image.get("alt") or "").strip():
            errors.append("Missing descriptive alt on an image")
    for source in parsed.images + parsed.sources:
        for attr in ("src", "srcset"):
            ref = (source.get(attr) or "").strip()
            if ref.startswith("./"):
                relative.add(ref[2:])
    for path in sorted(relative):
        item = ROOT / path
        if not item.is_file():
            errors.append(f"Missing local visual asset: {path}")
    for svg in (ROOT / "assets").glob("*.svg"):
        try:
            ET.parse(svg)
        except ET.ParseError as err:
            errors.append(f"Invalid SVG: {svg.name}: {err}")
    if len({p["slug"] for p in projects}) != len(projects):
        errors.append("Duplicate project slug in manifest")
    for project in projects:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", project["slug"]):
            errors.append("Invalid repository slug in public manifest")
        url = f"https://github.com/jviola1019/{project['slug']}"
        if url not in body:
            errors.append(f"Missing repository link: {project['slug']}")
    limit = data["activity_limit"]
    tracked = {p["slug"] for p in projects if p.get("activity")}
    if not isinstance(limit, int) or not 1 <= limit <= len(tracked):
        errors.append("Invalid activity limit")
    seen = {}
    ns = "{http://www.w3.org/2000/svg}"
    for suffix in ("dark", "light", "mobile-dark", "mobile-light"):
        path = ROOT / "assets" / f"activity-{suffix}.svg"
        if not path.is_file():
            errors.append(f"Missing activity asset: {path.name}")
            continue
        try:
            root = ET.parse(path).getroot()
            rows = [(g.attrib["data-repository"], dt.datetime.fromisoformat(g.attrib["data-committed-at"].replace("Z", "+00:00")))
                    for g in root.findall(f".//{ns}g") if g.get("data-repository") is not None]
            if len(rows) != limit:
                errors.append(f"{suffix}: {len(rows)} rows, expected {limit}")
            if not {r for r, _ in rows}.issubset(tracked):
                errors.append(f"{suffix}: unapproved project included")
            if len({r for r, _ in rows}) != len(rows):
                errors.append(f"{suffix}: duplicate project")
            times = [date.timestamp() for _, date in rows]
            if times != sorted(times, reverse=True):
                errors.append(f"{suffix}: commit order incorrect")
            seen[suffix] = rows
        except (ET.ParseError, ValueError, KeyError) as err:
            errors.append(f"{suffix}: cannot validate activity asset: {err}")
    if len(seen) == 4 and any(rows != seen["dark"] for rows in seen.values()):
        errors.append("Activity variants disagree about latest commits")
    for anchor in ("#selected-work", "#research-standard", "#project-activity"):
        if anchor not in body:
            errors.append(f"Missing navigation anchor {anchor}")
    if not (ROOT / "docs" / "PORTFOLIO_AUDIT.md").is_file():
        errors.append("Missing provenance audit")
    if errors:
        for msg in errors:
            print(f"FAIL: {msg}", file=sys.stderr)
        return 1
    print(f"PASS: {len(projects)} public project records, {len(parsed.images)} described images, {len(relative)} local assets, {limit} activity rows, 4 synchronized SVG views")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
