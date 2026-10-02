#!/usr/bin/env python3
"""Frozen aggregate golden cases for representative Sätila editions.

These values are derived from the current audited public EQ Timing bundles.
They intentionally contain no athlete identities. Purpose: detect subtle
calculation drift after frontend/engine changes even when pages still render.
"""
from __future__ import annotations
import collections,json,statistics,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"docs"/"data"

GOLDEN={
 "2025-trail43":{
   "results":163,"finishers":135,"median_finish":17986.43,
   "segments":[
    ("Start","Torrås",16.2,130,6392.97,29,101),
    ("Torrås","Almered",7.8,130,2580.25,29,101),
    ("Almered","Skolan",7.0,133,2857.27,32,101),
    ("Skolan","Ramhulta",6.0,134,2739.52,32,102),
    ("Ramhulta","Smälteryd",4.5,133,2653.66,32,101),
    ("Smälteryd","Mål",1.5,133,521.45,32,101)]},
 "2025-trail22":{
   "results":190,"finishers":160,"median_finish":8828.25,
   "segments":[
    ("Start","Skolan",9.6,156,3513.975,47,109),
    ("Skolan","Ramhulta",6.7,156,2402.13,47,109),
    ("Ramhulta","Smälteryd",4.2,156,2403.905,46,110),
    ("Smälteryd","Mål",1.5,156,505.39,46,110)]},
 "2025-ultra85":{
   "results":99,"finishers":79,"median_finish":44118.96,
   "segments":[
    ("Start","Navåsen",19.4,79,9279.26,22,57),
    ("Navåsen","Äskhult",30.6,78,16575.755,22,56),
    ("Äskhult","Lerbäck",18.0,77,8674.98,22,55),
    ("Lerbäck","Ramhulta",10.7,78,5038.13,22,56),
    ("Ramhulta","Smälteryd",4.8,79,3291.49,22,57),
    ("Smälteryd","Mål",1.5,79,620.43,22,57)]},
 "2023-trail43":{
   "results":103,"finishers":86,"median_finish":16938.065,
   "segments":[
    ("Start","Torrås",8.0,85,6054.81,15,70),
    ("Torrås","Almered",16.0,84,2434.15,15,69),
    ("Almered","Skolan",7.0,8,4164.615,4,4),
    ("Skolan","Ramhulta",6.0,8,4058.165,4,4),
    ("Ramhulta","Smälteryd",4.5,85,2581.4,15,70),
    ("Smälteryd","Mål",1.5,85,510.22,15,70)]},
 "2016-ultra85":{
   "results":72,"finishers":52,"median_finish":40570.34,
   "segments":[
    ("Start","Ramhulta",77.4,52,37597.41,2,50),
    ("Ramhulta","Mål",4.6,52,3426.31,2,50)]},
}

def race(key):
    return json.loads((ROOT/"races"/f"{key}.json").read_text(encoding="utf-8"))

def observed_summary(obj):
    counts=collections.Counter(x["station_uid"] for x in obj["splits"])
    bounds=[{"uid":"start","name":"Start","km":0}]+[
      s for s in sorted(obj["stations"],key=lambda x:(x["sort"],x.get("km") or 0))
      if s["is_analysis_boundary"] and isinstance(s.get("km"),(int,float)) and s["km"]>0 and counts[s["uid"]]>0]
    by=collections.defaultdict(dict)
    for x in obj["splits"]:by[x["result_id"]][x["station_uid"]]=x
    finish=[x for x in obj["results"] if x["status"]=="FINISHED" and x.get("finish_seconds",0)>0]
    segs=[]
    for i in range(1,len(bounds)):
        a,b=bounds[i-1],bounds[i]
        if b["km"]<=a["km"]:continue
        values=[];sex=collections.Counter()
        for p in finish:
            ta=0 if i==1 else by[p["id"]].get(a["uid"],{}).get("elapsed_seconds")
            tb=by[p["id"]].get(b["uid"],{}).get("elapsed_seconds")
            if ta is not None and tb is not None and tb>ta:
                values.append(tb-ta)
                if p.get("sex") in ("F","M"):sex[p["sex"]]+=1
        segs.append((a["name"],b["name"],round(b["km"]-a["km"],3),len(values),
                     round(statistics.median(values),3) if values else None,sex["F"],sex["M"]))
    return {"results":len(obj["results"]),"finishers":len(finish),
            "median_finish":round(statistics.median(p["finish_seconds"] for p in finish),3),
            "segments":segs}

class GoldenAggregateRegression(unittest.TestCase):
    def test_representative_real_edition_aggregates_are_stable(self):
        for key,expected in GOLDEN.items():
            got=observed_summary(race(key))
            self.assertEqual(got["results"],expected["results"],key)
            self.assertEqual(got["finishers"],expected["finishers"],key)
            self.assertAlmostEqual(got["median_finish"],expected["median_finish"],places=3,msg=key)
            self.assertEqual(len(got["segments"]),len(expected["segments"]),key)
            for actual,wanted in zip(got["segments"],expected["segments"]):
                self.assertEqual(actual[:4],wanted[:4],(key,actual,wanted))
                self.assertAlmostEqual(actual[4],wanted[4],places=3,msg=f"{key} {actual[:2]}")
                self.assertEqual(actual[5:],wanted[5:],(key,actual,wanted))

    def test_golden_cases_encode_known_method_edges(self):
        t=GOLDEN["2025-trail43"]["segments"]
        self.assertIn(("Start","Torrås",16.2,130,6392.97,29,101),t)
        self.assertFalse(any("Grind" in x[:2] for group in GOLDEN.values() for x in group["segments"]))
        sparse=[x for x in GOLDEN["2023-trail43"]["segments"] if x[3]==8]
        self.assertEqual(len(sparse),2)
        self.assertTrue(all(x[5:]==(4,4) for x in sparse))
        u=GOLDEN["2016-ultra85"]
        self.assertTrue(all(x[5]==2 for x in u["segments"]))

if __name__=="__main__":
    unittest.main(verbosity=2)
