#!/usr/bin/env python3
"""Independent edge-case regression for Sätila analytic semantics (stdlib unittest)."""
from __future__ import annotations
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from audit_statistics_reference import (
 empirical_quantile,readiness,source_anchored_segment,
 observed_goal_fraction,goal_plan_exact,observed_podium,observed_rank_progression)

class StatisticsContract(unittest.TestCase):
 def test_median_and_distribution_minima(self):
  for n in (0,1,3,4):
   d=readiness(list(range(1,n+1)))
   self.assertIsNone(d["median"])
  self.assertEqual(readiness([1,2,3,4,5])["median"],3)
  self.assertIsNone(readiness(list(range(1,10)))["q25"])
  self.assertEqual(readiness(list(range(1,11)))["q25"],3.25)
  self.assertIsNone(readiness(list(range(1,20)))["q10"])
  self.assertAlmostEqual(readiness(list(range(1,21)))["q10"],2.9)
  self.assertIsNone(empirical_quantile([1,float("nan"),float("inf"),2],.5,5))

 def test_no_invented_tostared_passage(self):
  # Real Grind and Torrås passages, but NO Tostared reading in source.
  self.assertEqual(source_anchored_segment(300,3900),3600)
  self.assertIsNone(source_anchored_segment(300,None))
  self.assertIsNone(source_anchored_segment(None,3900))
  self.assertIsNone(source_anchored_segment(3900,300))
  self.assertIsNone(source_anchored_segment(0,0))
  self.assertEqual(source_anchored_segment(0,300),300)

 def test_observed_fraction_with_true_runner_finish(self):
  self.assertAlmostEqual(observed_goal_fraction(3600,18000),.2)
  self.assertIsNone(observed_goal_fraction(None,18000))
  self.assertIsNone(observed_goal_fraction(18001,18000))
  self.assertIsNone(observed_goal_fraction(1800,None))

 def test_goal_seconds_sum_and_monotone_cumulative(self):
  plan=goal_plan_exact(21601,[[.19]*7,[.31]*8,[.5]*9],[4,7,11])
  self.assertEqual([r["method"] for r in plan],["observed_relative_median"]*3)
  self.assertEqual(sum(r["segment_seconds"] for r in plan),21601)
  self.assertEqual(plan[-1]["cumulative_seconds"],21601)
  self.assertEqual([r["cumulative_seconds"] for r in plan],
                   sorted(r["cumulative_seconds"] for r in plan))

 def test_fallback_is_labelled_and_exact(self):
  plan=goal_plan_exact(36001,[[.10]*6,[],[.60]*6],[2,6,12])
  self.assertEqual(plan[1]["source_n"],0)
  self.assertEqual(plan[1]["method"],"distance_only_planning_fallback")
  self.assertEqual(plan[0]["method"],"observed_relative_median")
  self.assertEqual(sum(r["segment_seconds"] for r in plan),36001)

 def test_all_fallback_never_claims_historical_coverage(self):
  plan=goal_plan_exact(6001,[[],[],[]],[2,3,5])
  self.assertEqual([r["method"] for r in plan],["distance_only_planning_fallback"]*3)
  self.assertEqual(sum(r["segment_seconds"] for r in plan),6001)

 def test_invalid_goal_and_negative_distance(self):
  for seconds in (0,-1,2.3,"3000",None):
   with self.assertRaises(ValueError):goal_plan_exact(seconds,[[.5]*5],[2])
  with self.assertRaises(ValueError):goal_plan_exact(200,[[.5]*5],[0])

 def test_podium_never_fabricates_bronze(self):
  actual=[{"id":"w1","seconds":400},{"id":"w2","seconds":500}]
  result=observed_podium(actual)
  self.assertEqual(len(result),2)
  self.assertEqual([r["id"] for r in result],["w1","w2"])
  self.assertEqual(len(observed_podium(actual,minimum_size=3)),0)
  repeats=actual+[{"id":"w1","seconds":550},{"id":"w3","seconds":600}]
  self.assertEqual([r["id"] for r in observed_podium(repeats)],["w1","w2","w3"])

 def test_rank_journey_no_imagined_start(self):
  self.assertIsNone(observed_rank_progression([]))
  self.assertIsNone(observed_rank_progression([{"name":"Start","place":None},{"name":"Grind","place":4}]))
  data=[{"name":"Start","place":None},{"name":"Grind","place":14},
        {"name":"Tostared","place":None},{"name":"Torrås","place":9},
        {"name":"Mål","place":5}]
  result=observed_rank_progression(data)
  self.assertEqual(result["net_places_gained"],9)
  self.assertEqual(result["observation_count"],3)
  self.assertEqual(result["first_observed"],("Grind",14))

if __name__=="__main__":
 unittest.main(verbosity=2)
