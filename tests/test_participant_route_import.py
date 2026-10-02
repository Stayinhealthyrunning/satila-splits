#!/usr/bin/env python3
"""Exercise isolated 2024 participant GPX import without adding invented production coordinates."""
from __future__ import annotations
import json
import shutil
import tempfile
import unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import promote_participant_gpx as module
from test_published_data_integrity import audit

class HistoricalRouteImport(unittest.TestCase):
    def test_single_year_gpx_and_partial_timing_are_independent(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)
            shutil.copytree(ROOT/"docs/data",target/"docs/data")
            (target/"config").mkdir()
            shutil.copyfile(ROOT/"config/source-registry.json",target/"config/source-registry.json")
            original_root,original_data=module.ROOT,module.DATA
            module.ROOT=target;module.DATA=target/"docs/data"
            try:
                before=json.loads((module.DATA/"races/2024-trail43.json").read_text())
                other=json.loads((module.DATA/"races/2023-trail43.json").read_text())
                gpx=target/"data/participant-gpx/trail43-2024.gpx"
                gpx.parent.mkdir(parents=True,exist_ok=True)
                # 180 invented fixture points ONLY in this temporary test directory.
                # The fixture is never committed as a real historic GPX.
                pts="".join(
                    f'<trkpt lat="{57.5+(0.0001 if i%2 else -0.0001):.6f}" lon="{12.3+i*0.7/179:.8f}"><ele>100</ele></trkpt>'
                    for i in range(180))
                gpx.write_text('<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1"><trk><trkseg>'+pts+'</trkseg></trk></gpx>',encoding="utf-8")
                module.promote(gpx,2024,"trail43")
                after=json.loads((module.DATA/"races/2024-trail43.json").read_text())
                route=json.loads((module.DATA/"routes/2024-trail43-participant.json").read_text())
                catalog=json.loads((module.DATA/"bootstrap.json").read_text())
                meta=next(e for e in catalog["editions"] if e["race_key"]=="2024-trail43")
                self.assertEqual(route["edition_references"],[2024])
                self.assertEqual(route["type"],"VERIFIED_PARTICIPANT")
                self.assertEqual(meta["route_file"],"routes/2024-trail43-participant.json")
                self.assertEqual(meta["route_status"],"participant_track_display_only")
                self.assertGreaterEqual(len(route["points"]),100)
                for label in ("results","splits","stations"):
                    self.assertEqual(before[label],after[label],label)
                self.assertEqual(other,json.loads((module.DATA/"races/2023-trail43.json").read_text()))
                self.assertFalse(any("timestamp" in str(key).lower() for key in route))
                audited=audit(module.DATA)
                self.assertEqual(audited["failures"],[],audited["failures"])
                self.assertEqual(audited["summary"]["participant_display_routes"],1)
            finally:
                module.ROOT,module.DATA=original_root,original_data

if __name__=="__main__":
    unittest.main(verbosity=2)
