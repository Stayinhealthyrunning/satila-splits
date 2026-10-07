"""Static contract guards for the Sätila Comparison 2.0 adapter.

Browser tests exercise the real DOM and synchronized route engine. These
guards make semantic drift (especially the A/B sign) fail quickly in source QA.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "docs/assets/app.js").read_text(encoding="utf-8")
CONTRACT = json.loads((ROOT / "config/comparison-compatibility-v2.json").read_text(encoding="utf-8"))


class ComparisonV2ContractTest(unittest.TestCase):
    def test_declared_capabilities_match_target(self):
        current = CONTRACT["current_capabilities"]
        target = CONTRACT["target_capabilities"]
        self.assertEqual(current, target)
        self.assertFalse(current["cross_edition_comparison"])
        self.assertFalse(current["team_entity"])

    def test_selection_cardinality_is_preserved(self):
        self.assertIn("S.mapDuel.length!==2", SOURCE)
        self.assertIn("S.mapDuel.length<2", SOURCE)
        self.assertIn("S.mapDuel.length<5", SOURCE)
        self.assertIn("runners.length<2||runners.length>5", SOURCE)

    def test_signed_gap_is_b_minus_a(self):
        self.assertIn("b.elapsed_seconds-a.elapsed_seconds", SOURCE)
        self.assertNotIn("a.elapsed_seconds-b.elapsed_seconds", SOURCE)
        self.assertIn("Lucka B−A", SOURCE)
        self.assertIn("positiv = A före", SOURCE)

    def test_kpi_placement_segment_and_field_layers_exist(self):
        for token in (
            "comparisonKpis",
            "placementSvg",
            "fieldComparisonSvg",
            "DUELLENS NYCKELTAL",
            "OFFICIELL PLACERINGSRESA",
            "SEGMENTDUELL",
            "RELATIV PRESTATION MOT FÄLTET",
        ):
            self.assertIn(token, SOURCE)
        self.assertIn("medianSeconds/a.seconds-1", SOURCE)
        self.assertIn("medianSeconds/b.seconds-1", SOURCE)
        self.assertIn("Dold · fysisk distans ej verifierad", SOURCE)
        self.assertIn("segmenttid mot fältmedian", SOURCE)

    def test_playback_audio_share_and_sparse_defaults(self):
        options = re.findall(r'<option value="(30|60|120|180)"', SOURCE)
        self.assertGreaterEqual(options.count("30"), 2)
        for value in ("30", "60", "120", "180"):
            self.assertGreaterEqual(options.count(value), 2)
        self.assertIn('<option value="120" selected>2 minuter</option>', SOURCE)
        self.assertIn('<option value="both" selected>Följ båda</option>', SOURCE)
        self.assertIn("const DEFAULT_VOLUME=.30", SOURCE)
        self.assertIn("compareA", SOURCE)
        self.assertIn("compareB", SOURCE)
        self.assertIn("compareTime", SOURCE)
        self.assertIn("compareSegment", SOURCE)
        self.assertIn("Förenklad verklig resa", SOURCE)
        self.assertIn("intermediate<2", SOURCE)
        self.assertIn("segmentRaw=params.get('compareSegment')", SOURCE)
        self.assertIn("segmentRaw!==null&&Number.isInteger(segment)", SOURCE)
        self.assertNotIn("drawCompareMap(x,y,S.duelD,clock);writeComparisonState", SOURCE)

    def test_placement_axis_agrees_with_place_one_on_top(self):
        self.assertIn("chartYTicks(L,W-R,T,H-B,maxPlace,1", SOURCE)


if __name__ == "__main__":
    unittest.main()
