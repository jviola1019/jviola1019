#!/usr/bin/env python3
"""Deterministic, offline tests for profile activity ordering and SVG rendering."""
from __future__ import annotations

import io
import json
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch

from render_activity import get_latest, newest_first, render, render_mobile


def item(slug: str, committed_at: str) -> dict[str, str]:
    return {
        "slug": slug,
        "label": slug.upper(),
        "date": "formatted date",
        "sha": "abcdef1",
        "committed_at": committed_at,
    }


class ActivityOrderingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.unsorted = [
            item("rae", "2026-09-08T03:12:49+00:00"),
            item("nfl", "2026-10-19T19:13:09+00:00"),
            item("nba", "2026-04-28T05:54:11+00:00"),
            item("gridiron", "2026-05-02T04:47:53+00:00"),
            item("gmat", "2025-12-19T04:23:56+00:00"),
        ]

    def test_descending_actual_commit_time_not_repository_order(self) -> None:
        self.assertEqual(
            [x["slug"] for x in newest_first(self.unsorted)],
            ["nfl", "rae", "gridiron", "nba", "gmat"],
        )

    def test_same_day_compares_seconds_not_pretty_dates(self) -> None:
        data = [item("early", "2026-10-21T08:00:01Z"), item("late", "2026-10-21T18:00:00Z")]
        self.assertEqual([x["slug"] for x in newest_first(data)], ["late", "early"])

    def test_equal_timestamps_are_deterministic(self) -> None:
        data = [item("z", "2026-01-01T00:00:00Z"), item("a", "2026-01-01T00:00:00Z")]
        self.assertEqual([x["slug"] for x in newest_first(data)], ["a", "z"])

    def test_renderer_sorts_even_when_called_unsorted(self) -> None:
        for theme in ("dark", "light"):
            for renderer in (render, render_mobile):
                svg = renderer(self.unsorted, theme)
                root = ET.fromstring(svg)
                ns = "{http://www.w3.org/2000/svg}"
                groups = [g for g in root.findall(f".//{ns}g") if g.get("data-repository")]
                self.assertEqual(
                    [g.get("data-repository") for g in groups],
                    ["nfl", "rae", "gridiron", "nba", "gmat"],
                )
                self.assertTrue(all(g.get("data-committed-at") for g in groups))
                self.assertIn("NEWEST → OLDEST", svg)

    def test_api_preserves_full_timestamp(self) -> None:
        response = {
            "sha": "0123456789abcdef",
            "commit": {"committer": {"date": "2026-10-21T16:44:09Z"}},
        }
        with patch("render_activity.urllib.request.urlopen", return_value=io.BytesIO(json.dumps([response]).encode())):
            value = get_latest("Example", "example_repo")
        self.assertEqual(value["sha"], "0123456")
        self.assertEqual(value["committed_at"], "2026-10-21T16:44:09+00:00")
        self.assertEqual(value["date"], "Oct 21, 2026")

    def test_svg_escapes_untrusted_labels(self) -> None:
        svg = render([dict(item("safe", "2026-01-01T00:00:00Z"), label='Mock & <Demo>')], "dark")
        ET.fromstring(svg)
        self.assertIn("Mock &amp; &lt;Demo&gt;", svg)


if __name__ == "__main__":
    unittest.main()
