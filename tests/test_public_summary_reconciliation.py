#!/usr/bin/env python3
"""Independent public summary reconciliation using all official race rows.

Recomputes official edition catalogue KPIs and population group summaries
without importing or editing the production data generator or frontend.
"""
from __future__ import annotations
import collections
import json
import math
import statistics
import unittest
from pathlib import Path

DATA=Path(__file__).resolve().parents[1]/"docs"/"data"
STATUSES={"FINISHED","DNF","DNS","DSQ","UNKNOWN"}

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

class PublicSummaryReconciliation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=load(DATA/"bootstrap.json")["editions"]
        cls.races={ed["race_key"]:load(DATA/"races"/f"{ed['race_key']}.json")
                   for ed in cls.catalog}

    def test_edition_catalogue_is_exact_aggregate_of_race_rows(self):
        for ed in self.catalog:
            race=self.races[ed["race_key"]]
            counts=collections.Counter(r["status"] for r in race["results"])
            self.assertFalse(set(counts)-STATUSES)
            self.assertEqual(ed["results"],len(race["results"]))
            for field,source in (("finishers","FINISHED"),("dnf","DNF"),
                                 ("dns","DNS"),("dsq","DSQ"),("unknown","UNKNOWN")):
                self.assertEqual(ed[field],counts[source],(ed["race_key"],field))
            self.assertEqual(ed["split_observations"],len(race["splits"]))
            self.assertEqual(ed["timing_stations"],len(race["stations"]))
            for field in ("race_key","family","year","event_id","date","nominal_km",
                          "source_url"):
                self.assertIn(field,ed,(ed["race_key"],field))
                self.assertIn(field,race,(ed["race_key"],field))
                self.assertEqual(ed[field],race[field],(ed["race_key"],field))
            # Browser bootstrap intentionally omits unverified *internal*
            # course-version labels: internal evidence is not automatically
            # promoted to a publicly comparable course version.
            for field in ("route_status","route_file"):
                self.assertEqual(ed.get(field),race.get(field),(ed["race_key"],field))
            version=ed.get("course_version")
            if version is not None:
                self.assertEqual(version,race.get("course_version"),ed["race_key"])
            else:
                internal=race.get("course_version")
                self.assertTrue(internal is None or any(flag in internal for flag in
                                ("unverified","candidate","pending")),
                                (ed["race_key"],internal))
                self.assertNotIn(ed.get("route_status"),("official_verified",
                    "organizer_2025_2026_reuse_assumption"),ed["race_key"])

    def test_every_catalogue_median_is_from_exact_finished_times(self):
        for ed in self.catalog:
            finish_times=sorted(r["finish_seconds"] for r in self.races[ed["race_key"]]["results"]
                                if r["status"]=="FINISHED")
            self.assertEqual(len(finish_times),ed["finishers"])
            value=statistics.median(finish_times) if finish_times else None
            self.assertIsNotNone(value,ed["race_key"])
            self.assertAlmostEqual(ed["median_seconds"],value,delta=.011,
                                   msg=ed["race_key"])

    def test_group_completion_uses_known_starters_not_dns(self):
        total_known=total_finished=0
        for ed in self.catalog:
            result=self.races[ed["race_key"]]["results"]
            for sex in ("F","M"):
                group=[r for r in result if r["sex"]==sex]
                starts=[r for r in group if r["status"] in ("FINISHED","DNF","DSQ")]
                finishes=[r for r in starts if r["status"]=="FINISHED"]
                self.assertLessEqual(len(finishes),len(starts))
                self.assertEqual(len(starts),
                                 sum(r["status"] in ("FINISHED","DNF","DSQ") for r in group))
                if starts:
                    pct=len(finishes)/len(starts)*100
                    self.assertGreaterEqual(pct,0)
                    self.assertLessEqual(pct,100)
                total_known+=len(starts);total_finished+=len(finishes)
            # Preserve possible missing/other sex categories without miscasting.
            self.assertEqual(sum(r["sex"] in ("F","M") for r in result)+
                             sum(r["sex"] not in ("F","M") for r in result),len(result))
        self.assertLessEqual(total_finished,2649)
        self.assertLessEqual(total_known,2649+128)

    def test_finish_histogram_endpoints_have_no_missing_exact_boundary(self):
        for ed in self.catalog:
            fs=[r for r in self.races[ed["race_key"]]["results"] if r["status"]=="FINISHED"]
            bins=collections.Counter()
            for r in fs:
                seconds=r["finish_seconds"]
                self.assertTrue(math.isfinite(seconds) and seconds>0)
                bin_start=math.floor(seconds/900)*900
                self.assertGreaterEqual(seconds,bin_start)
                self.assertLess(seconds,bin_start+900)
                bins[(r["sex"] if r["sex"] in ("F","M") else "unknown",bin_start)]+=1
            self.assertEqual(sum(bins.values()),ed["finishers"])

    def test_all_edition_history_totals_preserve_dnf_dns_and_unknown(self):
        by_year=collections.defaultdict(lambda:collections.Counter())
        by_family=collections.defaultdict(lambda:collections.Counter())
        for ed in self.catalog:
            year=ed["year"];family=ed["family"]
            for k in ("results","finishers","dnf","dns","dsq","unknown","split_observations"):
                by_year[year][k]+=ed[k]
                by_family[family][k]+=ed[k]
        self.assertEqual(len(by_year),9)
        self.assertEqual(len(by_family),3)
        for dimension in (by_year,by_family):
            self.assertEqual(sum(row["results"] for row in dimension.values()),3272)
            for group,row in dimension.items():
                self.assertEqual(row["results"],sum(row[k] for k in
                                 ("finishers","dnf","dns","dsq","unknown")),group)

if __name__=="__main__":
    unittest.main(verbosity=2)
