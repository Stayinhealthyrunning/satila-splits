#!/usr/bin/env python3
"""Independent acceptance: 2023 43 km display height is spatially transferred from 2024.

This is a visual-only altitude replacement. The original 2023 normalized GPX
and JSON remain immutable in data/normalized-gpx. Race edition and EQ split
data must not be altered. Both participant tracks are geometrically near
identical, but no assertion of officially certified course equivalence is made.
"""
from __future__ import annotations

import json
import math
import statistics
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ROUTES=ROOT/"docs"/"data"/"routes"
ORIGINAL=ROOT/"data"/"normalized-gpx"/"trail43-2023-2025-normalized.json"
P23=ROUTES/"2023-trail43-participant.json"
P24=ROUTES/"2024-trail43-participant.json"
REF_SHA="d83bfad962e94a69ed0ea53a0c063679478234cccd3a780d714900ae7640c4b4"
SOURCE_SHA="0ea09c107612064a31c717462cebbfd092b6cefb728b051f529f7b8a27737695"
METRES_LON=111320*math.cos(math.radians(57.5))


def read(p:Path):
    return json.loads(p.read_text(encoding="utf-8"))


def xy(point):
    return ((point[2]-12.4)*METRES_LON,(point[1]-57.5)*111320)


def nearest_height(point,reference):
    x,y=xy(point)
    best_d=float("inf")
    best_z=None
    for a,b in zip(reference,reference[1:]):
        ax,ay=xy(a); bx,by=xy(b)
        vx,vy=bx-ax,by-ay
        length_sq=vx*vx+vy*vy
        f=max(0,min(1,((x-ax)*vx+(y-ay)*vy)/length_sq)) if length_sq else 0.
        dist=math.hypot(x-ax-f*vx,y-ay-f*vy)
        if dist<best_d:
            best_d=dist
            best_z=a[3]+f*(b[3]-a[3])
    return best_d,round(best_z,2)


def short_jumps(points):
    return [abs(b[3]-a[3]) for a,b in zip(points,points[1:])
            if 0<(b[0]-a[0])*1000<=100]


class SpatialTransferredHeight(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current=read(P23)
        cls.original=read(ORIGINAL)
        cls.reference=read(P24)

    def test_only_altitude_changed_from_approved_original(self):
        current=self.current
        original=self.original
        self.assertEqual(current["source_sha256"],SOURCE_SHA)
        self.assertEqual(current["race_key"],"2023-trail43")
        self.assertEqual(current["edition_references"],[2023])
        self.assertEqual(current["geometry_length_km"],original["geometry_length_km"])
        self.assertEqual(len(current["points"]),len(original["points"])==822)
        self.assertEqual([p[:3] for p in current["points"]],[p[:3] for p in original["points"]])
        self.assertEqual(current["normalized_source_group"],"trail43-2023-2025-normalized")
        self.assertFalse(any("timestamp" in k.lower() or "runner" in k.lower() for k in current))

    def test_exact_geographic_height_reproduction_and_match_distance(self):
        origin=self.current["elevation_provenance"]
        self.assertEqual(origin["type"],"SPATIALLY_TRANSFERRED_PARTICIPANT_GPX")
        self.assertEqual(origin["reference_year"],2024)
        self.assertEqual(origin["reference_source_sha256"],REF_SHA)
        self.assertEqual(self.reference["source_sha256"],REF_SHA)
        self.assertEqual(origin["reference_route_file"],"routes/2024-trail43-participant.json")
        self.assertTrue(origin["not_original_2023_gpx_altitude"])
        self.assertTrue(origin["not_official_ascent_or_runner_altitude"])
        matches=[nearest_height(p,self.reference["points"]) for p in self.current["points"]]
        self.assertTrue(all(d<24 for d,_ in matches),max(d for d,_ in matches))
        self.assertTrue(all(abs(p[3]-z)<.011 for p,(_,z) in zip(self.current["points"],matches)))
        self.assertTrue(all(isinstance(p[3],(int,float)) and math.isfinite(p[3])
                            for p in self.current["points"]))
        self.assertLessEqual(max(d for d,_ in matches),origin["match_distance_limit_m"])
        print("MATCH 2023-to-2024 max horizontal distance",round(max(d for d,_ in matches),2),"m")

    def test_noise_reduced_without_overwriting_2024_or_2025(self):
        before=short_jumps(self.original["points"])
        after=short_jumps(self.current["points"])
        self.assertGreaterEqual(sum(v>20 for v in before),20)
        self.assertLessEqual(sum(v>20 for v in after),1)
        self.assertLess(statistics.quantiles(after,n=20)[-1],6)
        self.assertEqual(self.reference["edition_references"],[2024])
        boot=read(ROOT/"docs"/"data"/"bootstrap.json")
        rows={x["race_key"]:x for x in boot["editions"]}
        self.assertEqual(rows["2023-trail43"]["route_file"],"routes/2023-trail43-participant.json")
        self.assertEqual(rows["2024-trail43"]["route_file"],"routes/2024-trail43-participant.json")
        self.assertEqual(rows["2025-trail43"]["route_file"],"routes/trail43-2025-2026.json")

    def test_disclosure_in_public_page_logic(self):
        script=(ROOT/"docs"/"assets"/"app.js").read_text(encoding="utf-8")
        self.assertIn("Överförd GPX-höjd (2024)",script)
        self.assertIn("Inte originalhöjd från 2023",script)
        self.assertIn("SPATIALLY_TRANSFERRED_PARTICIPANT_GPX",script)


if __name__=="__main__":
    unittest.main(verbosity=2)
