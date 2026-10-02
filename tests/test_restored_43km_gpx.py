#!/usr/bin/env python3
"""Permanent acceptance for the five restored, owner-approved trail43 source GPX."""
import hashlib,json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"docs/data"
ORIGINAL_SHA={
 2021:"d07051fda67d4343ccf9ff49ec7ee8788b923965f14b127e5d7ffaac91a0c9d6",
 2022:"b7bd4710327fae74d0478db5dbb1df80c3bb7f84c9d316fd9c2a86028486479c",
 2023:"60b5f920d6f4e652db1760120f6d22bd1fcdea722edee46c83dc7d6f0c1e04da",
 2024:"d83bfad962e94a69ed0ea53a0c063679478234cccd3a780d714900ae7640c4b4",
 2025:"f090e7d461e0ae53e06561c340b1a87bab30f10454e49ebaface2cd19468502b",
}
DERIVED={
"trail43-2021-2022":("2a681e80841ae008872e35d8f4ffd1617b80a94bebcbbb18881e52fd86af82d4",44.30917,1090),
"trail43-2023-2025":("0ea09c107612064a31c717462cebbfd092b6cefb728b051f529f7b8a27737695",41.873734,822),
}
def read(path):return json.loads(path.read_text(encoding="utf-8"))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

class RestoredOriginals(unittest.TestCase):
 def test_five_original_files_match_original_uploads(self):
  for y,sha in ORIGINAL_SHA.items():
   path=ROOT/f"data/participant-gpx/trail43-{y}.gpx"
   self.assertTrue(path.is_file(),str(path))
   self.assertEqual(digest(path),sha,str(path))
 def test_normalized_family_reconstruction_is_checksum_locked(self):
  for group,(sha,length,points) in DERIVED.items():
   path=ROOT/f"data/normalized-gpx/{group}-normalized.gpx"
   asset=read(ROOT/f"data/normalized-gpx/{group}-normalized.json")
   self.assertEqual(digest(path),sha)
   self.assertAlmostEqual(asset["geometry_length_km"],length,places=5)
   self.assertEqual(len(asset["points"]),points)
   self.assertTrue(all(b[0]>a[0] for a,b in zip(asset["points"],asset["points"][1:])))
 def test_all_2021_to_2025_trail43_editions_have_verifiable_display_maps(self):
  editions={e["race_key"]:e for e in read(DATA/"bootstrap.json")["editions"]}
  inventory={item.get("race_key"):item for item in read(DATA/"route-inventory.json")}
  coverage={e["race_key"]:e for e in read(DATA/"coverage.json")}
  for year in range(2021,2026):
   key=f"{year}-trail43";e=editions[key];self.assertTrue(e.get("route_file"),key)
   route=read(DATA/e["route_file"])
   self.assertTrue(len(route["points"])>=100,key)
   if year<2025:
    self.assertEqual(route["type"],"VERIFIED_PARTICIPANT",key)
    self.assertEqual(route["edition_references"],[year],key)
    self.assertEqual(e["route_source_sha256"],route["source_sha256"],key)
    self.assertEqual(coverage[key]["route_sha256"],route["source_sha256"],key)
    self.assertEqual(inventory[key]["source_sha256"],route["source_sha256"],key)
   else:self.assertEqual(route["type"],"OFFICIAL_ORGANIZER",key)
  # The 2024 year-scoped recorded route and 2025 organizer route remain intact.
  self.assertEqual(editions["2024-trail43"]["route_file"],"routes/2024-trail43-participant.json")
  self.assertEqual(editions["2025-trail43"]["route_file"],"routes/trail43-2025-2026.json")
 def test_no_source_timing_rows_changed(self):
  allr=[read(p) for p in (DATA/"races").glob("*.json")]
  self.assertEqual(sum(len(r["results"]) for r in allr),3272)
  self.assertEqual(sum(len(r["splits"]) for r in allr),14466)  # 16525 raw TIME − 2059 owner-rejected Grind rows

if __name__=="__main__":unittest.main(verbosity=2)
