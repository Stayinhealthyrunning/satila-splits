#!/usr/bin/env python3
"""Independent real-data regression for all 27 Sätila analytical editions.

This test deliberately reads the frozen published JSON but does not modify it.
The statistical oracle is Python/stdlib and does not depend on the production
JavaScript. It is intended for integration CI after Codex changes presentation.
"""
from __future__ import annotations
import collections
import json
import math
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from audit_statistics_reference import (
 goal_plan_exact, observed_goal_fraction, observed_podium, readiness,
 source_anchored_segment, observed_rank_progression
)

DATA=ROOT/"docs"/"data"

def read(p):
    return json.loads(p.read_text(encoding="utf-8"))

def edition(key):
    return read(DATA/"races"/f"{key}.json")

def observed_segments(race):
    """Build analysis pairs using only globally observed public TIME anchors.

    Source station metadata is not removed from the underlying race record.
    PRE/FV technical stations are not promoted to analysis boundaries.
    """
    count=collections.Counter(s["station_uid"] for s in race["splits"])
    stations=[s for s in sorted(race["stations"],key=lambda x:(x["sort"],x.get("km") or 0))
              if s["is_analysis_boundary"] and isinstance(s.get("km"),(int,float))
              and s["km"]>0 and count[s["uid"]]>0]
    boundary=[{"uid":"start","name":"Start","km":0}]+stations
    readings=collections.defaultdict(dict)
    for row in race["splits"]:
        readings[row["result_id"]][row["station_uid"]]=row
    finishers=[r for r in race["results"] if r["status"]=="FINISHED" and r["finish_seconds"] and r["finish_seconds"]>0]
    segments=[]
    for i,(a,b) in enumerate(zip(boundary,boundary[1:])):
        km=b["km"]-a["km"]
        if km<=0:continue
        obs=[]
        for runner in finishers:
            own=readings[runner["id"]]
            start=0 if a["uid"]=="start" else own.get(a["uid"],{}).get("elapsed_seconds")
            end=own.get(b["uid"],{}).get("elapsed_seconds")
            seconds=source_anchored_segment(start,end)
            if seconds is not None:
                frac=observed_goal_fraction(seconds,runner["finish_seconds"])
                if frac is not None:
                    obs.append({"id":runner["id"],"sex":runner["sex"],"seconds":seconds,
                                "goal_fraction":frac,"name":runner["name"]})
        segments.append({"from":a["name"],"to":b["name"],"km":km,"observations":obs})
    return finishers,readings,segments

class RealSourceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=read(DATA/"bootstrap.json")["editions"]
        cls.races={e["race_key"]:edition(e["race_key"]) for e in cls.catalog}

    def test_all_27_editions_have_exclusively_source_based_segments(self):
        self.assertEqual(len(self.races),27)
        examined=0
        for key,race in self.races.items():
            finishers,reading,segments=observed_segments(race)
            self.assertGreaterEqual(len(segments),1,key)
            for seg in segments:
                self.assertGreater(seg["km"],0)
                for o in seg["observations"]:
                    self.assertGreater(o["seconds"],0,key)
                    self.assertLessEqual(o["goal_fraction"],1.0)
                    self.assertIn(o["id"],reading,key)
                    examined+=1
            self.assertTrue(all(len(s["observations"])<=len(finishers) for s in segments))
        self.assertGreater(examined,5000,"Expected substantial exact public timing coverage")

    def test_stats_and_podium_thresholds_are_per_real_segment_and_sex(self):
        for key,race in self.races.items():
            _,_,segments=observed_segments(race)
            for seg in segments:
                xs=[x["seconds"] for x in seg["observations"]]
                stats=readiness(xs)
                self.assertEqual(stats["n"],len(xs))
                self.assertEqual(stats["median"] is not None,len(xs)>=5,(key,seg["to"]))
                self.assertEqual(stats["q25"] is not None,len(xs)>=10,(key,seg["to"]))
                self.assertEqual(stats["q10"] is not None,len(xs)>=20,(key,seg["to"]))
                for sex in ("F","M"):
                    subset=[o for o in seg["observations"] if o["sex"]==sex]
                    self.assertEqual(len(observed_podium(subset)),min(3,len(subset)))
                    self.assertEqual(readiness([o["seconds"] for o in subset])["median"] is not None,
                                     len(subset)>=5,(key,seg["to"],sex))

    def test_goal_plans_all_27_finish_exactly_with_declared_fallbacks(self):
        for key,race in self.races.items():
            _,_,segments=observed_segments(race)
            fractions=[[o["goal_fraction"] for o in seg["observations"]] for seg in segments]
            kms=[seg["km"] for seg in segments]
            for goal in (3601,21601,43201):
                plan=goal_plan_exact(goal,fractions,kms)
                self.assertEqual(plan[-1]["cumulative_seconds"],goal,key)
                self.assertEqual(sum(x["segment_seconds"] for x in plan),goal,key)
                self.assertEqual(len(plan),len(segments),key)
                for row,seg in zip(plan,segments):
                    self.assertEqual(row["source_n"],len(seg["observations"]))
                    wanted="observed_relative_median" if row["source_n"]>=5 else "distance_only_planning_fallback"
                    self.assertEqual(row["method"],wanted,(key,seg["to"]))

    def test_2025_trail43_uses_real_grind_torras_bridge(self):
        race=self.races["2025-trail43"]
        self.assertEqual(len([x for x in race["splits"] if x["station_uid"]==1416266]),0)
        _,_,segments=observed_segments(race)
        bridge=[s for s in segments if s["from"]=="Grind" and s["to"]=="Torrås"]
        self.assertEqual(len(bridge),1)
        self.assertAlmostEqual(bridge[0]["km"],15.0)
        self.assertEqual(len(bridge[0]["observations"]),130)
        self.assertFalse(any(s["to"]=="Tostared" or s["from"]=="Tostared" for s in segments))
        self.assertEqual(len(segments),7)

    def test_2023_two_sparse_segments_are_not_overinterpreted(self):
        _,_,segments=observed_segments(self.races["2023-trail43"])
        for first,last in (("Almered","Skolan"),("Skolan","Ramhulta")):
            x=next(s for s in segments if s["from"]==first and s["to"]==last)
            self.assertEqual(len(x["observations"]),8)
            self.assertEqual(collections.Counter(o["sex"] for o in x["observations"])["F"],4)
            self.assertEqual(collections.Counter(o["sex"] for o in x["observations"])["M"],4)
            self.assertIsNotNone(readiness([o["seconds"] for o in x["observations"]])["median"])
            self.assertIsNone(readiness([o["seconds"] for o in x["observations"]])["q25"])
            self.assertIsNone(readiness([o["seconds"] for o in x["observations"] if o["sex"]=="F"])["median"])

    def test_2016_ultra_podium_has_only_two_real_women(self):
        race=self.races["2016-ultra85"]
        women=[{"id":r["id"],"seconds":r["finish_seconds"]} for r in race["results"]
               if r["status"]=="FINISHED" and r["sex"]=="F"]
        self.assertEqual(len(women),2)
        self.assertEqual(len(observed_podium(women)),2)

    def test_placement_progression_requires_observed_stations(self):
        eligible=0
        for key,race in self.races.items():
            _,readings,_=observed_segments(race)
            for runner in race["results"]:
                if runner["status"]!="FINISHED":continue
                rs=readings.get(runner["id"],{})
                checkpoints=[{"name":s["name"],"place":rs.get(s["uid"],{}).get("place")}
                             for s in sorted(race["stations"],key=lambda s:s["sort"]) if s["is_analysis_boundary"]]
                j=observed_rank_progression(checkpoints)
                if j:
                    eligible+=1
                    self.assertGreaterEqual(j["observation_count"],2)
                    self.assertGreater(j["first_observed"][1],0)
                    # A genuine public station can itself be named Start. Do not
                    # forbid source observations; forbid invented positions.
                    if j["first_observed"][0]=="Start":
                        self.assertTrue(any(
                            st["name"]=="Start" and st["uid"] in rs and
                            rs[st["uid"]].get("place")==j["first_observed"][1]
                            for st in race["stations"]
                        ),(key,runner["id"]))
        self.assertGreater(eligible,2000)

if __name__=="__main__":
    unittest.main(verbosity=2)
