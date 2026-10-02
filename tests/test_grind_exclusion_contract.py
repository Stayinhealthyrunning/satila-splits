#!/usr/bin/env python3
"""Owner-approved exclusion of the nonofficial 1.2 km Grind measurement.

The original EQ Timing source archive and 27 results tables remain immutable.
The public analytical view has NO Grind station or Grind TIME row. All 20
affected edition catalogues, timing counts, splits and derived analysis must
instead reflect the remaining checkpoints. This must remain true on rebuild.
"""
from __future__ import annotations
import json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"docs"/"data"
REMOVED={
 "2018-trail22":(1060718,110),"2018-trail43":(1060719,55),"2018-ultra85":(1060677,74),
 "2019-trail22":(1086370,125),"2019-trail43":(1086371,80),"2019-ultra85":(1086353,72),
 "2021-trail22":(1160506,173),"2021-trail43":(1160507,88),
 "2022-trail22":(1204558,171),"2022-trail43":(1204559,89),"2022-ultra85":(1217495,40),
 "2023-trail22":(1249840,138),"2023-trail43":(1249841,86),"2023-ultra85":(1249850,61),
 "2024-trail22":(1299913,154),"2024-trail43":(1299914,100),"2024-ultra85":(1299923,69),
 "2025-trail22":(1361394,160),"2025-trail43":(1361395,135),"2025-ultra85":(1361404,79),
}
RAW_OBSERVATIONS=16525
REMOVED_OBSERVATIONS=2059
PUBLISHED_OBSERVATIONS=14466


def load(p):return json.loads(p.read_text(encoding="utf-8"))


class ExcludeOwnerRejectedGrind(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.boot={v["race_key"]:v for v in load(DATA/"bootstrap.json")["editions"]}
        cls.coverage={v["race_key"]:v for v in load(DATA/"coverage.json")}
        cls.races={k:load(DATA/"races"/f"{k}.json") for k in cls.boot}

    def test_exactly_20_affected_editions_and_2059_filtered_time_observations(self):
        self.assertEqual(len(REMOVED),20)
        self.assertEqual(sum(count for _,count in REMOVED.values()),REMOVED_OBSERVATIONS)
        self.assertEqual(RAW_OBSERVATIONS-REMOVED_OBSERVATIONS,PUBLISHED_OBSERVATIONS)
        self.assertEqual(len(self.races),27)
        self.assertEqual(sum(len(r["results"]) for r in self.races.values()),3272)
        self.assertEqual(sum(len(r["splits"]) for r in self.races.values()),PUBLISHED_OBSERVATIONS)

    def test_no_excluded_station_or_time_remains_in_any_public_edition(self):
        for key,race in self.races.items():
            boot=self.boot[key];coverage=self.coverage[key]
            uids={s["uid"] for s in race["stations"]}
            self.assertEqual(len(uids),len(race["stations"]),key)
            self.assertFalse(any(s["name"].strip().casefold()=="grind" for s in race["stations"]),key)
            self.assertFalse(any("grind" in str(s["name"]).casefold() for s in race["stations"]),key)
            self.assertEqual(len(race["stations"]),boot["timing_stations"],key)
            self.assertEqual(len(race["stations"]),coverage["timing_stations"],key)
            self.assertEqual(len(race["splits"]),boot["split_observations"],key)
            self.assertEqual(len(race["splits"]),coverage["split_observations"],key)
            self.assertEqual({s["result_id"] for s in race["splits"]}&
                             {r["id"] for r in race["results"]},
                             {s["result_id"] for s in race["splits"]},key)
            self.assertTrue(all(s["station_uid"] in uids for s in race["splits"]),key)
            if key in REMOVED:
                uid,removed=REMOVED[key]
                self.assertNotIn(uid,uids,key)
                self.assertTrue(all(s["station_uid"]!=uid for s in race["splits"]),key)
                self.assertEqual(len(race["splits"])+removed,
                                 boot["split_observations"]+removed,key)
            self.assertEqual(sum(1 for s in race["stations"] if s["is_finish"]),1,key)

    def test_next_true_station_is_first_valid_2025_segment_anchor(self):
        for family,next_station,next_km,expected_n in (
            ("trail43","Torrås",16.2,130),
            ("trail22","Skolan",9.6,156),
            ("ultra85","Navåsen",19.4,79),
        ):
            race=self.races[f"2025-{family}"]
            stations=[s for s in race["stations"] if s["is_analysis_boundary"] and s["km"]>0]
            first=min(stations,key=lambda s:s["km"])
            # Tostared is metadata-only and must never become an observed segment.
            observations={s["station_uid"] for s in race["splits"]}
            first=next(s for s in sorted(stations,key=lambda s:s["km"]) if s["uid"] in observations)
            self.assertEqual((first["name"],first["km"]),(next_station,next_km))
            full={r["id"] for r in race["results"] if r["status"]=="FINISHED"}
            n=sum(s["station_uid"]==first["uid"] and s["result_id"] in full
                  for s in race["splits"])
            self.assertEqual(n,expected_n,(family,n))

    def test_rebuild_source_policy_and_public_assets_cannot_reintroduce_grind(self):
        builder=(ROOT/"tools"/"build_satila.py").read_text(encoding="utf-8")
        self.assertIn("casefold()!='grind'",builder)
        for p in (DATA/"bootstrap.json",DATA/"coverage.json"):
            self.assertNotIn('"Grind"',p.read_text(encoding="utf-8"))
        self.assertEqual(len(load(DATA/"source-fingerprints.json")),9)
        self.assertNotIn('"Grind"',(ROOT/"docs"/"assets"/"app.js").read_text(encoding="utf-8"))


if __name__=="__main__":unittest.main(verbosity=2)
