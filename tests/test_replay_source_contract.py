#!/usr/bin/env python3
"""Real-data and synthetic tests of source-aware map, elevation and duel scrub."""
from __future__ import annotations
import json
import math
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from audit_replay_reference import (
 build_anchors,time_at_display_km,duel_time_gap,position_at_display_km)

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

class ReplaySemantics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.races={f:load(ROOT/"docs"/"data"/"races"/f"2025-{f}.json") for f in ("trail43","trail22")}
        cls.routes={f:load(ROOT/"docs"/"data"/"routes"/f"{f}-2025-2026.json") for f in cls.races}

    def test_both_2025_routes_have_exact_timing_anchors_for_every_finisher(self):
        tested=0
        for fam,race in self.races.items():
            route=self.routes[fam]
            for runner in race["results"]:
                if runner["status"]!="FINISHED":continue
                anchors=build_anchors(race,route,runner)
                self.assertGreaterEqual(len(anchors),2,(fam,runner["id"]))
                self.assertEqual(anchors[0]["kind"],"start_origin")
                self.assertAlmostEqual(anchors[0]["seconds"],0)
                self.assertTrue(all(a["seconds"]<b["seconds"] and a["display_km"]<b["display_km"]
                                    for a,b in zip(anchors,anchors[1:])))
                for a in anchors[1:]:
                    observed=time_at_display_km(anchors,a["display_km"])
                    self.assertIsNotNone(observed)
                    self.assertAlmostEqual(observed[0],a["seconds"],places=5)
                    self.assertEqual(observed[1],"source_observation")
                self.assertLessEqual(anchors[-1]["display_km"],route["geometry_length_km"]+1e-6)
                self.assertIsNone(time_at_display_km(anchors,route["geometry_length_km"]+0.1))
                tested+=1
        self.assertGreater(tested,200)

    def test_tostared_and_nonofficial_grind_are_not_replay_anchors(self):
        fam="trail43";race=self.races[fam];route=self.routes[fam]
        best=next(r for r in race["results"] if r["status"]=="FINISHED" and r["place"]==1)
        anchors=build_anchors(race,route,best)
        self.assertFalse(any(a["station_uid"]==1416266 for a in anchors))
        self.assertFalse(any(a["name"]=="Grind" for a in anchors))
        torras=next(a for a in anchors if a["name"]=="Torrås")
        artificial_position=10.2/race["nominal_km"]*route["geometry_length_km"]
        self.assertGreater(torras["display_km"],artificial_position)
        self.assertEqual(anchors[0]["kind"],"start_origin")
        estimate=time_at_display_km(anchors,artificial_position)
        self.assertIsNotNone(estimate)
        self.assertEqual(estimate[1],"illustrative_between_observed_anchors")
        self.assertGreater(estimate[0],0)
        self.assertLess(estimate[0],torras["seconds"])

    def test_interpolation_and_gap_do_not_extrapolate(self):
        anchors=[{"display_km":0,"seconds":0,"kind":"start_origin"},
                 {"display_km":3,"seconds":900,"kind":"source_observation"},
                 {"display_km":7,"seconds":2300,"kind":"source_observation"}]
        self.assertEqual(time_at_display_km(anchors,0),(0,"start_origin"))
        self.assertEqual(time_at_display_km(anchors,3),(900,"source_observation"))
        self.assertEqual(time_at_display_km(anchors,5),(1600,"illustrative_between_observed_anchors"))
        self.assertIsNone(time_at_display_km(anchors,-0.1))
        self.assertIsNone(time_at_display_km(anchors,7.1))
        self.assertIsNone(time_at_display_km(anchors,float("nan")))
        b=[{"display_km":0,"seconds":0,"kind":"start_origin"},
           {"display_km":7,"seconds":2100,"kind":"source_observation"}]
        for km in (0,2,3,5,7):
            gap=duel_time_gap(anchors,b,km)
            self.assertAlmostEqual(gap,-duel_time_gap(b,anchors,km),places=8)
            self.assertAlmostEqual(duel_time_gap(anchors,anchors,km),0,places=8)
        self.assertIsNone(duel_time_gap(anchors,b,7.1))

    def test_real_duel_requires_both_athletes_to_have_time_anchor(self):
        race=self.races["trail43"];route=self.routes["trail43"]
        finishers=sorted((r for r in race["results"] if r["status"]=="FINISHED"),key=lambda r:r["finish_seconds"])
        a=build_anchors(race,route,finishers[0]);b=build_anchors(race,route,finishers[1])
        self.assertAlmostEqual(duel_time_gap(a,b,0),0)
        # Where both have a finish anchor, the displayed finish gap must
        # equal the source's real finish time difference.
        end=route["geometry_length_km"]
        self.assertAlmostEqual(duel_time_gap(a,b,end),
                               finishers[0]["finish_seconds"]-finishers[1]["finish_seconds"],places=4)
        self.assertEqual(time_at_display_km(a,end)[1],"source_observation")
        self.assertIsNone(duel_time_gap(a,b,end+0.001))

    def test_map_cursor_only_uses_route_geometry_not_athlete_gps(self):
        for fam,route in self.routes.items():
            pts=route["points"]
            for km in (0,pts[-1][0]/4,pts[-1][0]/2,pts[-1][0]):
                actual=position_at_display_km(pts,km)
                self.assertIsNotNone(actual,(fam,km))
                self.assertAlmostEqual(actual[0],km)
                self.assertTrue(56<=actual[1]<=59)
                self.assertTrue(11<=actual[2]<=14)
            self.assertIsNone(position_at_display_km(pts,-.01))
            self.assertIsNone(position_at_display_km(pts,pts[-1][0]+.01))
            self.assertIsNone(position_at_display_km(pts,float("inf")))

    def test_no_unauthorized_historic_runner_replay(self):
        race=dict(self.races["trail43"])
        race["year"]=2024
        runner=next(r for r in race["results"] if r["status"]=="FINISHED")
        self.assertEqual(build_anchors(race,self.routes["trail43"],runner),[])
        race["year"]=2025
        race["route_file"]=None
        self.assertEqual(build_anchors(race,self.routes["trail43"],runner),[])
        race["route_file"]="routes/trail43-2025-2026.json"
        wrong_route=dict(self.routes["trail43"],family="trail22")
        self.assertEqual(build_anchors(race,wrong_route,runner),[])

if __name__=="__main__":
    unittest.main(verbosity=2)
