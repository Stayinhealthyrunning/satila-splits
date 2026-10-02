#!/usr/bin/env python3
"""Explicit course comparability contract for historical Sätila editions.

Course evidence must be checked separately from timing availability. In the
current draft only organizer 2025→2026 route reuse is approved for 5/10/21/43.
Owner-accepted normalized 43 km participant geometry (2021–2022, 2023–2025)
is valid for year-scoped display, but never an official course or permission
for automatic cross-year timing-performance comparisons.
"""
from __future__ import annotations
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"docs"/"data"

def read(file):
    return json.loads(file.read_text(encoding="utf-8"))

def promoted_group(ed):
    """No implicit race-family, race-distance or overlapping candidate shortcut."""
    version=ed.get("course_version")
    status=ed.get("route_status")
    if not version or status not in ("organizer_2025_2026_reuse_assumption","official_verified"):
        return None
    if any(word in version for word in ("unverified","candidate","pending")):
        return None
    return version

def whole_course_comparable(first,second):
    """Compare across years only with an EXPLICIT mutually promoted version."""
    ga=promoted_group(first);gb=promoted_group(second)
    return bool(ga and ga==gb and first["family"]==second["family"])

def display_route_authorized(family,year,inventory):
    matches=[r for r in inventory if r["family"]==family and r.get("type")=="OFFICIAL_ORGANIZER"]
    return len(matches)==1 and year in matches[0]["edition_references"]

class CourseComparabilityContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.boot=read(DATA/"bootstrap.json")
        cls.editions=cls.boot["editions"]
        cls.route_inventory=read(DATA/"route-inventory.json")
        cls.participant_versions=read(ROOT/"config"/"course-versions.json")

    def test_historical_years_are_source_supported(self):
        self.assertEqual({e["year"] for e in self.editions},
                         {2016,2017,2018,2019,2021,2022,2023,2024,2025})
        self.assertFalse(any(e["year"]==2026 for e in self.editions),
                         "A future official course is NOT a future result archive")

    def test_no_authoritative_2026_ultra_85_backfill(self):
        self.assertTrue(display_route_authorized("ultra85",2026,self.route_inventory))
        self.assertFalse(display_route_authorized("ultra85",2025,self.route_inventory))
        self.assertFalse(display_route_authorized("ultra85",2024,self.route_inventory))

    def test_organizer_2025_2026_is_explicit_for_four_routes(self):
        for family in ("trail5","trail10","trail22","trail43"):
            self.assertTrue(display_route_authorized(family,2025,self.route_inventory))
            self.assertTrue(display_route_authorized(family,2026,self.route_inventory))
            self.assertFalse(display_route_authorized(family,2024,self.route_inventory))

    def test_current_older_editions_do_not_silently_borrow_modern_route(self):
        for ed in self.editions:
            if ed["year"]<2025:
                if ed.get("route_file"):
                    self.assertEqual(ed.get("route_status"),"participant_track_display_only",ed["race_key"])
                    source=read(DATA/ed["route_file"])
                    self.assertEqual(source.get("edition_references"),[ed["year"]])
                    self.assertIn(source.get("type"),("VERIFIED_PARTICIPANT","TRACE_DE_TRAIL"))
                self.assertFalse(promoted_group(ed),ed["race_key"])
        e43=next(e for e in self.editions if e["race_key"]=="2025-trail43")
        e22=next(e for e in self.editions if e["race_key"]=="2025-trail22")
        self.assertIsNotNone(promoted_group(e43))
        self.assertIsNotNone(promoted_group(e22))

    def test_same_nominal_distance_is_not_course_evidence(self):
        a={"family":"trail43","nominal_km":43,"course_version":None,
           "route_status":"none"}
        b={"family":"trail43","nominal_km":43,"course_version":None,
           "route_status":"none"}
        self.assertFalse(whole_course_comparable(a,b))
        b["course_version"]="trail43-2025-2026-organizer-assumed"
        b["route_status"]="organizer_2025_2026_reuse_assumption"
        self.assertFalse(whole_course_comparable(a,b))

    def test_promoted_matching_course_version_enables_only_same_family(self):
        a={"family":"trail43","course_version":"official-v1",
           "route_status":"official_verified"}
        b={"family":"trail43","course_version":"official-v1",
           "route_status":"official_verified"}
        self.assertTrue(whole_course_comparable(a,b))
        b["family"]="trail22"
        self.assertFalse(whole_course_comparable(a,b))
        b["family"]="trail43";b["course_version"]="official-v2"
        self.assertFalse(whole_course_comparable(a,b))

    def test_participant_normalized_routes_are_owner_accepted_for_display_only(self):
        candidates=self.participant_versions["normalized_route_candidates"]
        self.assertTrue(candidates)
        self.assertTrue(all(c.get("status")=="OWNER_ACCEPTED_FOR_YEAR_SCOPED_DISPLAY"
                            for c in candidates.values()))
        for year,obj in self.participant_versions["year_candidates"].items():
            self.assertIn(int(year),{2021,2022,2023,2024,2025})
            self.assertIn(obj["comparison_group"],candidates)
        # Owner acceptance permits display but not automatic whole-course timing comparison.
        a={"family":"trail43","course_version":"trail43-2023-2025",
           "route_status":"participant_track_display_only"}
        self.assertIsNone(promoted_group(a))

    def test_route_geometry_distance_is_not_timing_distance(self):
        r43=next(x for x in self.route_inventory if x["family"]=="trail43" and x.get("type")=="OFFICIAL_ORGANIZER")
        r22=next(x for x in self.route_inventory if x["family"]=="trail22" and x.get("type")=="OFFICIAL_ORGANIZER")
        e43=next(e for e in self.editions if e["race_key"]=="2025-trail43")
        e22=next(e for e in self.editions if e["race_key"]=="2025-trail22")
        self.assertAlmostEqual(r43["geometry_length_km"],42.254,places=2)
        self.assertEqual(e43["nominal_km"],43)
        self.assertNotAlmostEqual(r43["geometry_length_km"],e43["nominal_km"],places=1)
        self.assertAlmostEqual(r22["geometry_length_km"],23.043,places=2)
        self.assertEqual(e22["nominal_km"],22)
        self.assertNotAlmostEqual(r22["geometry_length_km"],e22["nominal_km"],places=1)

if __name__=="__main__":
    unittest.main(verbosity=2)
