#!/usr/bin/env python3
"""Permanent integrity gate for seven historical ultra85 race-day map routes."""
import hashlib,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/"docs/data"
SHA={
2018:"5f0864fba534b23d48ac2adde73240bd58d48946d4a2cb092757a9b4304175ec",
2019:"4b508c9071480feea7823ca8df371cf39030b74d62370851df8de485fbce9510",
2021:"13c033f0e4a336334f9030ea322f4df3df226415c850896fd511e980e36ed294",
2022:"0b6cd4a39ecce9fe6262f03b8c9be15c59c6428277c0b67497402d95d95207b0",
2023:"e363954507767a4a06f74f4547d4e5b7216849452317f4359c368ecd28636e81",
2024:"042ddbb7d32862fbcc415f284577f3dad8225adec47f1240e9dd9caa7f7f18c6",
2025:"d54db03d752dd1e6679492f595aa6121c4396d94ed13c9903f5a974b11380d47"}
POINTS={2018:1618,2019:1345,2021:964,2022:1607,2023:796,2024:1158,2025:856}
KM={2018:84.148,2019:81.152,2021:82.775,2022:84.211,2023:81.049,2024:83.364,2025:81.414}
def read(p):return json.loads(p.read_text(encoding="utf-8"))
class Ultra85History(unittest.TestCase):
 def test_checksum_pinned_encoded_payload_is_not_raw_gpx(self):
  p=ROOT/"data/derived/ultra85-2018-2025-sanitized.zlib.b64"
  self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),"a565fe9209450c06e7407ead0c9414507b35783fe23f5a2a855b428aec9dcb46")
  self.assertNotIn(b"<trkpt",p.read_bytes())
 def test_all_seven_year_specific_routes_are_ready(self):
  bootstrap={x["race_key"]:x for x in read(DATA/"bootstrap.json")["editions"]}
  coverage={x["race_key"]:x for x in read(DATA/"coverage.json")}
  inventory={x.get("race_key"):x for x in read(DATA/"route-inventory.json")}
  for year,sha in SHA.items():
   key=f"{year}-ultra85"; ed=bootstrap[key];route=read(DATA/ed["route_file"])
   self.assertEqual(ed["route_file"],f"routes/{key}-participant.json")
   self.assertEqual(ed["route_status"],"participant_track_display_only")
   self.assertEqual(ed["route_source_sha256"],sha)
   self.assertEqual(route["race_key"],key)
   self.assertEqual(route["edition_references"],[year])
   self.assertEqual(route["type"],"TRACE_DE_TRAIL" if year==2022 else "VERIFIED_PARTICIPANT")
   self.assertEqual(route["source_sha256"],sha)
   self.assertEqual(len(route["points"]),POINTS[year])
   self.assertAlmostEqual(route["geometry_length_km"],KM[year],delta=.025)
   self.assertEqual(route["elevation_status"],"not_in_source")
   self.assertTrue(all(len(p)==4 and p[3] is None for p in route["points"]))
   self.assertTrue(all(b[0]>a[0] for a,b in zip(route["points"],route["points"][1:])))
   self.assertEqual(coverage[key]["route_sha256"],sha)
   self.assertEqual(inventory[key]["source_sha256"],sha)
   self.assertNotIn("timestamps",route)
   self.assertNotIn("participant_name",route)
  for year in (2016,2017):self.assertFalse(bootstrap[f"{year}-ultra85"].get("route_file"))
 def test_official_eqtiming_observations_unchanged(self):
  races=[read(p) for p in (DATA/"races").glob("*.json")]
  self.assertEqual(len(races),27)
  self.assertEqual(sum(len(r["results"]) for r in races),3272)
  self.assertEqual(sum(len(r["splits"]) for r in races),16525)
if __name__=="__main__":unittest.main(verbosity=2)
