#!/usr/bin/env python3
"""Regression contract for the seven accepted historical Ultra85 display routes."""
from __future__ import annotations

import hashlib
import json
import math
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data"
EXPECTED = {
    2018: (1618, 84.147947, "5f0864fba534b23d48ac2adde73240bd58d48946d4a2cb092757a9b4304175ec", 368, "da505d1f04039ce66323dd132d450fc6dc291277d611575ad3b934cc5d5d5681"),
    2019: (1345, 81.151690, "4b508c9071480feea7823ca8df371cf39030b74d62370851df8de485fbce9510", 426, "d0aa9c67bb2842ce3d640dadaf8355902ea37aae601dcdee7c1d8c7c5d083aaa"),
    2021: (964, 82.775276, "13c033f0e4a336334f9030ea322f4df3df226415c850896fd511e980e36ed294", 228, "4526543d83b81fcccf11b67e63002a94dfb67a632198264487941a4341259360"),
    2022: (1607, 84.210529, "0b6cd4a39ecce9fe6262f03b8c9be15c59c6428277c0b67497402d95d95207b0", 352, "abefef3ae2989adce6bd0bff67079550f8d3cde2742f284e590d4ecedfdf7a65"),
    2023: (796, 81.048957, "e363954507767a4a06f74f4547d4e5b7216849452317f4359c368ecd28636e81", 540, "36974771651fcffec49c83de8233560b798930d6d69f8f0b9547dfbb303be86e"),
    2024: (1158, 83.364334, "042ddbb7d32862fbcc415f284577f3dad8225adec47f1240e9dd9caa7f7f18c6", 615, "5b7ec074b6a900fdf03d2d5ecfab5a28540217ca9bddce928ba9fa71d5f83abe"),
    2025: (856, 81.413504, "d54db03d752dd1e6679492f595aa6121c4396d94ed13c9903f5a974b11380d47", 709, "5b5c73510c755f6adef7bde1aee55b3940ad498319ce99c559437ff44c833fd1"),
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(value) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class HistoricalUltra85Routes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.editions = {row["race_key"]: row for row in load(DATA / "bootstrap.json")["editions"]}
        cls.coverage = {row["race_key"]: row for row in load(DATA / "coverage.json")}
        cls.inventory = {row.get("race_key"): row for row in load(DATA / "route-inventory.json")}

    def test_metadata_is_year_locked_and_synchronized(self):
        for year, (point_count, length, source_sha, _, _) in EXPECTED.items():
            key = f"{year}-ultra85"
            edition = self.editions[key]
            race = load(DATA / "races" / f"{key}.json")
            coverage = self.coverage[key]
            inventory = self.inventory[key]
            route = load(DATA / edition["route_file"])
            for row in (edition, race, coverage):
                self.assertEqual(row["route_status"], "participant_track_display_only", key)
                self.assertEqual(row["route_file"], f"routes/{key}-participant.json", key)
                self.assertEqual(row["route_source_sha256"], source_sha, key)
                self.assertEqual(row["measured_route_geometry_km"], length, key)
            self.assertEqual(coverage["route_sha256"], source_sha, key)
            self.assertEqual(coverage["route_source_type"], "VERIFIED_PARTICIPANT", key)
            self.assertEqual(route["race_key"], key)
            self.assertEqual(route["edition_references"], [year])
            self.assertEqual(route["source_sha256"], inventory["source_sha256"])
            self.assertEqual(len(route["points"]), point_count)
            self.assertAlmostEqual(route["geometry_length_km"], length, places=6)

    def test_missing_elevation_is_explicit_and_safe(self):
        app = (ROOT / "docs" / "assets" / "app.js").read_text(encoding="utf-8")
        self.assertIn("Höjddata saknas i detta historiska deltagarspår", app)
        self.assertIn("Höjddata saknas i källspåret", app)
        for year in EXPECTED:
            key = f"{year}-ultra85"
            route = load(DATA / "routes" / f"{key}-participant.json")
            self.assertFalse(self.inventory[key]["elevation_available"], key)
            self.assertTrue(all(point[3] is None for point in route["points"]), key)
            self.assertTrue(all(math.isfinite(point[0]) for point in route["points"]), key)

    def test_participant_timestamps_never_become_official_splits(self):
        split_fields = {"result_id", "station_uid", "elapsed_seconds", "place"}
        for year, (_, _, _, split_count, split_sha) in EXPECTED.items():
            key = f"{year}-ultra85"
            race = load(DATA / "races" / f"{key}.json")
            route = load(DATA / "routes" / f"{key}-participant.json")
            self.assertFalse(any("time" in field.lower() for field in route), key)
            self.assertNotIn("timestamps", route, key)
            self.assertEqual(len(race["splits"]), split_count, key)
            self.assertEqual(digest(race["splits"]), split_sha, key)
            self.assertTrue(all(set(split) == split_fields for split in race["splits"]), key)
            station_ids = {station["uid"] for station in race["stations"]}
            self.assertTrue(all(split["station_uid"] in station_ids for split in race["splits"]), key)


if __name__ == "__main__":
    unittest.main(verbosity=2)
