#!/usr/bin/env python3
"""Deterministic tests for curated project activity; no live API calls."""
from __future__ import annotations

import io
import json
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch

from render_activity import get_latest, load_manifest, newest_first, render, render_mobile


def item(slug: str, date: str) -> dict[str, str]:
    return {"slug": slug, "label": slug.upper(), "date": "Oct 21, 2026",
            "sha": "abcdef1", "committed_at": date}


class ActivityTests(unittest.TestCase):
    def setUp(self):
        self.items = [
            item("rae", "2026-09-08T03:12:49+00:00"),
            item("nfl", "2026-11-05T20:30:14+00:00"),
            item("nba", "2026-04-28T05:54:11+00:00"),
            item("gridiron", "2026-05-02T04:47:53+00:00"),
            item("redraft", "2026-11-20T03:10:23+00:00"),
            item("epoch", "2026-11-20T02:12:48+00:00"),
        ]

    def test_commit_time_sort_and_tie_break(self):
        ordered = newest_first(self.items)
        self.assertEqual([x["slug"] for x in ordered],
                         ["redraft", "epoch", "nfl", "rae", "gridiron", "nba"])
        self.assertEqual([x["slug"] for x in newest_first([
            item("z", "2026-01-01T00:00:00Z"),
            item("a", "2026-01-01T00:00:00Z")])], ["a", "z"])

    def test_all_renderings_are_same_order_and_valid_xml(self):
        expected = [x["slug"] for x in newest_first(self.items)]
        for theme in ("dark", "light"):
            for fn in (render, render_mobile):
                svg = fn(list(reversed(self.items)), theme)
                root = ET.fromstring(svg)
                groups = [g for g in root.findall(".//{http://www.w3.org/2000/svg}g")
                          if g.get("data-repository") is not None]
                self.assertEqual([g.get("data-repository") for g in groups], expected)
                self.assertIn("DEFAULT-BRANCH COMMITS", svg)
                self.assertIn("newest default-branch commit", svg)
                self.assertNotIn("<script", svg)

    def test_api_timestamp_preserved(self):
        response = {"sha": "0123456789abcdef",
                    "commit": {"committer": {"date": "2026-10-21T16:44:09Z"}}}
        with patch("render_activity.urllib.request.urlopen",
                   return_value=io.BytesIO(json.dumps([response]).encode())):
            value = get_latest("Example", "example")
        self.assertEqual(value["sha"], "0123456")
        self.assertEqual(value["committed_at"], "2026-10-21T16:44:09+00:00")

    def test_escapes_untrusted_label(self):
        sample = [dict(item("safe", "2026-01-01T00:00:00Z"), label="Demo & <Mock>")]
        self.assertIn("Demo &amp; &lt;Mock&gt;", render(sample, "light"))
        ET.fromstring(render_mobile(sample, "dark"))

    def test_manifest_has_curated_public_projects(self):
        tracked, limit = load_manifest()
        self.assertGreaterEqual(len(tracked), limit)
        self.assertEqual(limit, 6)
        self.assertTrue(any(slug == "redraft" for _, slug in tracked))
        self.assertFalse(any("prediction-market" in slug for _, slug in tracked))


if __name__ == "__main__":
    unittest.main()
