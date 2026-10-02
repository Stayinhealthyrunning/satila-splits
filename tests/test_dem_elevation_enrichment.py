#!/usr/bin/env python3
"""Pure-stdlib fail-closed tests for the optional offline DEM enrichment engine."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from enrich_route_elevation import enrich_route  # noqa: E402


class ElevationEnrichmentTests(unittest.TestCase):
    def setUp(self):
        self.route = {
            "family": "ultra85",
            "race_key": "2023-ultra85",
            "source_sha256": "a" * 64,
            "geometry_length_km": 81.048957,
            "elevation_available": False,
            "points": [
                [0.0, 57.5, 12.4, None],
                [0.4, 57.51, 12.41, None],
                [0.8, 57.52, 12.42, None],
            ],
        }
        self.opts = {
            "dem_source_id": "fixture-dem-1",
            "vertical_datum": "fixture-metres",
            "input_sha256": "b" * 64,
        }

    def test_complete_sampling_preserves_immutable_source_fields(self):
        result, qa = enrich_route(
            self.route, lambda lat, lon: 100 + (lat - 57.5) * 1000,
            **self.opts,
        )
        self.assertEqual([p[3] for p in result["points"]], [100.0, 110.0, 120.0])
        self.assertEqual([p[:3] for p in result["points"]], [p[:3] for p in self.route["points"]])
        self.assertEqual(self.route["points"][0][3], None, "input must not be mutated")
        self.assertEqual(result["source_sha256"], "a" * 64)
        self.assertEqual(result["geometry_length_km"], 81.048957)
        self.assertEqual(result["elevation_provenance"]["input_route_sha256"], "b" * 64)
        self.assertEqual(result["elevation_provenance"]["type"], "DEM_RECONSTRUCTED_TERRAIN")
        self.assertTrue(result["elevation_available"])
        self.assertEqual(qa["status"], "COMPLETE")
        self.assertEqual(qa["coverage_fraction"], 1.0)

    def test_incomplete_dem_produces_no_publishable_changes(self):
        result, qa = enrich_route(
            self.route,
            lambda lat, lon: None if lat > 57.50 else 105,
            **self.opts,
        )
        self.assertEqual(result, self.route)
        self.assertEqual(qa["status"], "BLOCKED_INCOMPLETE_DEM_COVERAGE")
        self.assertEqual(qa["covered_points"], 1)
        self.assertEqual(qa["no_data_indices"], [1, 2])

    def test_original_altitude_is_not_overwritten(self):
        self.route["points"][1][3] = 10
        with self.assertRaisesRegex(ValueError, "already includes elevation"):
            enrich_route(self.route, lambda lat, lon: 999, **self.opts)

    def test_missing_dem_provenance_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "provenance"):
            enrich_route(
                self.route, lambda lat, lon: 100,
                dem_source_id="", vertical_datum="unknown", input_sha256="b" * 64,
            )


if __name__ == "__main__":
    unittest.main()
