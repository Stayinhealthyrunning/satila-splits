#!/usr/bin/env python3
"""Targeted integration review for Codex-derived coverage.json.

Validates that new public coverage fields are pure derivations from already
committed race bundles + route inventory and do not invent new source facts.
"""
from __future__ import annotations
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"docs"/"data"

def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))

class CodexCoverageDerivation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.coverage=load(DATA/"coverage.json")
        cls.boot=load(DATA/"bootstrap.json")["editions"]
        cls.routes=load(DATA/"route-inventory.json")
        cls.by={x["race_key"]:x for x in cls.coverage}

    def test_exact_27_editions_no_loss_or_duplication(self):
        self.assertEqual(len(self.coverage),27)
        self.assertEqual(len(self.by),27)
        self.assertEqual(set(self.by),{e["race_key"] for e in self.boot})

    def test_all_new_counts_are_exact_derivations_from_race_rows(self):
        for ed in self.boot:
            c=self.by[ed["race_key"]]
            race=load(DATA/"races"/f"{ed['race_key']}.json")
            rows=race["results"]
            expected={
                "sex_f":sum(r.get("sex")=="F" for r in rows),
                "sex_m":sum(r.get("sex")=="M" for r in rows),
                "age_known":sum(isinstance(r.get("age"),int) for r in rows),
                "class_known":sum(bool(r.get("class_name")) for r in rows),
                "club_known":sum(bool(r.get("club")) for r in rows),
                "status_known":sum(r.get("status")!="UNKNOWN" for r in rows),
                "known_starters":sum(r.get("status") in ("FINISHED","DNF","DSQ") for r in rows),
            }
            expected["sex_known"]=expected["sex_f"]+expected["sex_m"]
            for k,v in expected.items():
                self.assertEqual(c[k],v,(ed["race_key"],k,c[k],v))
            for field in ("results","finishers","dnf","dns","dsq","unknown","split_observations","timing_stations",
                          "median_seconds","source_url","nominal_km","date","event_id","family","year","label"):
                self.assertEqual(c[field],ed[field],(ed["race_key"],field))

    def test_route_provenance_is_joined_only_from_authorized_inventory(self):
        for ed in self.boot:
            c=self.by[ed["race_key"]]
            route=next((r for r in self.routes
                        if ed.get("route_file") and r["family"]==ed["family"] and ed["year"] in r["edition_references"]),None)
            self.assertEqual(c.get("route_status"),ed.get("route_status","none"),ed["race_key"])
            self.assertEqual(c.get("course_version"),ed.get("course_version"),ed["race_key"])
            self.assertEqual(c.get("whole_course_comparison_group"),ed.get("whole_course_comparison_group"),ed["race_key"])
            expected={
              "route_source_type": route.get("type") if route else None,
              "route_source_filename": route.get("source_filename") if route else None,
              "route_sha256": route.get("source_sha256") if route else None,
              "route_geometry_km": route.get("geometry_length_km") if route else None,
              "route_evidence_note": route.get("evidence_note") if route else None,
            }
            for k,v in expected.items():
                self.assertEqual(c.get(k),v,(ed["race_key"],k))

    def test_known_route_edge_cases(self):
        c43=self.by["2025-trail43"]
        c22=self.by["2025-trail22"]
        c85=self.by["2025-ultra85"]
        self.assertEqual(c43["route_status"],"organizer_2025_2026_reuse_assumption")
        self.assertEqual(c22["route_status"],"organizer_2025_2026_reuse_assumption")
        self.assertIsNotNone(c43["route_sha256"])
        self.assertIsNotNone(c22["route_sha256"])
        self.assertEqual(c85["route_status"],"none")
        self.assertIsNone(c85["route_sha256"])
        self.assertIsNone(c85["route_geometry_km"])

if __name__=="__main__":
    unittest.main(verbosity=2)
