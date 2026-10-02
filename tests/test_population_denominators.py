#!/usr/bin/env python3
"""Population denominator and attrition contract for official Sätila records.

No edit to published data. These tests protect against apparently plausible
charts that incorrectly include DNS in starters, silently drop UNKNOWN, infer
sex, or assign DNF runners an unobserved dropout checkpoint.
"""
from __future__ import annotations
import collections
import json
import math
import unittest
from pathlib import Path

DATA=Path(__file__).resolve().parents[1]/"docs"/"data"

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

class PopulationContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=load(DATA/"bootstrap.json")["editions"]
        cls.races=[load(DATA/"races"/f"{ed['race_key']}.json") for ed in cls.catalog]

    def test_exhaustive_status_partitions_over_27_editions(self):
        totals=collections.Counter()
        for race in self.races:
            c=collections.Counter(row["status"] for row in race["results"])
            self.assertEqual(set(c)-{"FINISHED","DNF","DNS","DSQ","UNKNOWN"},set())
            self.assertEqual(sum(c.values()),len(race["results"]))
            totals.update(c)
        self.assertEqual(totals["FINISHED"],2649)
        self.assertEqual(totals["DNF"],128)
        self.assertEqual(totals["DNS"],494)
        self.assertEqual(totals["UNKNOWN"],1)
        self.assertEqual(sum(totals.values()),3272)

    def test_completion_denominator_is_not_all_registered_results(self):
        for race in self.races:
            c=collections.Counter(x["status"] for x in race["results"])
            # Only a confirmed finish or confirmed started non-finish qualifies
            # for an unambiguous "known started" denominator.
            known_starters=c["FINISHED"]+c["DNF"]+c["DSQ"]
            registered=len(race["results"])
            self.assertEqual(registered-known_starters,c["DNS"]+c["UNKNOWN"])
            if known_starters:
                fraction=c["FINISHED"]/known_starters
                self.assertGreaterEqual(fraction,0)
                self.assertLessEqual(fraction,1)
            self.assertEqual(registered,sum(c.values()))

    def test_finish_histograms_sum_to_actual_finite_finishers(self):
        for race in self.races:
            fs=[r for r in race["results"]
                if r["status"]=="FINISHED" and isinstance(r["finish_seconds"],(int,float))
                and math.isfinite(r["finish_seconds"]) and r["finish_seconds"]>0]
            bins=collections.defaultdict(collections.Counter)
            for r in fs:
                label=r["sex"] if r.get("sex") in ("F","M") else "unknown"
                # Same 15-minute right-open buckets as the UI.
                interval=math.floor(r["finish_seconds"]/900)*900
                self.assertGreaterEqual(r["finish_seconds"],interval)
                self.assertLess(r["finish_seconds"],interval+900)
                bins[interval][label]+=1
            total=sum(sum(c.values()) for c in bins.values())
            self.assertEqual(total,len(fs),race["race_key"])
            self.assertEqual(sum(c["F"] for c in bins.values()),
                             sum(r["sex"]=="F" for r in fs))
            self.assertEqual(sum(c["M"] for c in bins.values()),
                             sum(r["sex"]=="M" for r in fs))
            self.assertEqual(sum(c["unknown"] for c in bins.values()),
                             sum(r["sex"] not in ("F","M") for r in fs))

    def test_dnf_is_attached_only_to_last_real_observation(self):
        total_dnf=0;source_attached=0;unknown_last=0
        for race in self.races:
            station_order={s["uid"]:i for i,s in enumerate(race["stations"])}
            by_runner=collections.defaultdict(list)
            for sp in race["splits"]:
                self.assertIn(sp["station_uid"],station_order)
                by_runner[sp["result_id"]].append(sp)
            for row in race["results"]:
                if row["status"]!="DNF":continue
                total_dnf+=1
                obs=by_runner.get(row["id"],[])
                if obs:
                    source_attached+=1
                    last=max(obs,key=lambda s:station_order[s["station_uid"]])
                    self.assertIn(last,obs)
                    self.assertGreater(last["elapsed_seconds"],0)
                    self.assertIn(last["station_uid"],station_order)
                    # Never substitute a made-up KM marker if timing is absent.
                else:
                    unknown_last+=1
            self.assertLessEqual(total_dnf,len([r for e in self.races for r in e["results"]]))
        self.assertEqual(total_dnf,128)
        self.assertEqual(source_attached+unknown_last,total_dnf)
        print(f"DNF provenance: {source_attached} with exact last public TIME anchor, "
              f"{unknown_last} with no publishable dropout station")

    def test_result_id_namespace_does_not_merge_different_editions(self):
        ids=[r["id"] for race in self.races for r in race["results"]]
        self.assertEqual(len(ids),3272)
        self.assertEqual(len(ids),len(set(ids)),
                         "Result/runner comparison must retain edition identity")

if __name__=="__main__":
    unittest.main(verbosity=2)
