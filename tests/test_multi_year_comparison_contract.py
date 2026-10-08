#!/usr/bin/env python3
"""Contract guards for the separate Sätila multi-year comparison layer."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data"
SOURCE = (ROOT / "docs" / "assets" / "multi-year-comparison.js").read_text(encoding="utf-8")
INDEX = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
COMPARISON = json.loads((ROOT / "config" / "comparison-compatibility-v2.json").read_text(encoding="utf-8"))


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def promoted_group(edition):
    version = edition.get("course_version")
    status = edition.get("route_status")
    if not version or status not in ("organizer_2025_2026_reuse_assumption", "official_verified"):
        return None
    if any(word in version for word in ("unverified", "candidate", "pending")):
        return None
    return version


class MultiYearComparisonContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.boot = read(DATA / "bootstrap.json")
        cls.editions = cls.boot["editions"]

    def test_ui_has_all_year_search_and_separate_dialog(self):
        self.assertIn('id="multi-year-year"', INDEX)
        self.assertIn(">Alla år<", INDEX)
        self.assertIn("Jämför lopp på kartan", INDEX)
        self.assertIn('id="map-duel-builder"', INDEX)
        self.assertIn('id="multi-year-comparison" hidden', INDEX)
        self.assertNotIn('class="section multi-year-section-shell"', INDEX)
        self.assertIn('id="multi-year-dialog"', INDEX)
        self.assertIn("multi-year-map.js", INDEX)
        self.assertIn("multi-year-comparison.js", INDEX)

    def test_separate_layer_does_not_relax_comparison_2_replay_contract(self):
        self.assertFalse(COMPARISON["current_capabilities"]["cross_edition_comparison"])
        self.assertIn("wholeCourseComparable", SOURCE)
        self.assertIn("route_status", SOURCE)
        self.assertIn("organizer_2025_2026_reuse_assumption", SOURCE)
        self.assertIn("official_verified", SOURCE)
        self.assertIn("fältindex", SOURCE.lower())
        self.assertIn("rangordnas inte mot varandra", SOURCE)

    def test_current_historical_43km_years_are_not_silently_promoted(self):
        years = {2021, 2022, 2023, 2024, 2025}
        editions = [e for e in self.editions if e["family"] == "trail43" and e["year"] in years]
        self.assertEqual({e["year"] for e in editions}, years)
        promoted = {e["year"]: promoted_group(e) for e in editions}
        self.assertIsNotNone(promoted[2025])
        for year in (2021, 2022, 2023, 2024):
            self.assertIsNone(promoted[year])

    def test_real_repeated_runner_exists_for_cross_year_user_flow(self):
        seen = {}
        for year in (2021, 2022, 2023, 2024, 2025):
            race = read(DATA / "races" / f"{year}-trail43.json")
            for row in race["results"]:
                name = str(row.get("name") or "").strip()
                if name:
                    seen.setdefault(name, set()).add(year)
        repeated = {name: years for name, years in seen.items() if len(years) >= 2}
        self.assertTrue(repeated)
        self.assertTrue(any(len(years) >= 4 for years in repeated.values()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
