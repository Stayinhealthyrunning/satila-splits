#!/usr/bin/env python3
"""Safety checks for the owner-approved original + reconstructed normalized GPX import."""
from pathlib import Path
import hashlib,json,unittest
from zipfile import ZipFile
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"docs/data"
ARCHIVE=ROOT/"data/participant-gpx/satila-43km-2021-2025-source-and-normalized.zip"
EARLY="a41883b1157314a6a101a74bf2627f05dfb0ba9cbf24257571b3c8fd9a592f75"
LATE="90abb0279946528af88e807057e6000163b423583363a0d7739b19ae61165d80"
SHA={
 2021:"d07051fda67d4343ccf9ff49ec7ee8788b923965f14b127e5d7ffaac91a0c9d6",
 2022:"b7bd4710327fae74d0478db5dbb1df80c3bb7f84c9d316fd9c2a86028486479c" if False else "b7bd4710327fae74d0478db5dbb1df80c3bb7f84c9d316fd9c2a86028486479c",
 2023:"60b5f920d6f4e652db1760120f6d22bd1fcdea722edee46c83dc7d6f0c1e04da",
 2024:"d83bfad962e94a69ed0ea53a0c063679478234cccd3a780d714900ae7640c4b4",
 2025:"f090e7d461e0ae53e06561c340b1a87bab30f10454e49ebaface2cd19468502b",
}
def read(path):return json.loads(path.read_text(encoding="utf-8"))
class Normalized43kmImportContract(unittest.TestCase):
 @unittest.skipUnless(ARCHIVE.exists(),"Source archive ZIP not committed yet; import workflow runs after upload")
 def test_archive_originals_and_normalized_route_assets(self):
  archive_hash=hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
  self.assertEqual(archive_hash,"1617c1e1fe96912409989f3844f89c52e3673e8386c44394f1e0f367dd8cd5dc")
  with ZipFile(ARCHIVE) as z:
   manifest=json.loads(z.read("SOURCE_MANIFEST.json"))
   self.assertEqual(set(map(int,manifest["originals"])),set(SHA))
   for y,sha in SHA.items():
    f="original/"+manifest["originals"][str(y)]["file"]
    self.assertEqual(hashlib.sha256(z.read(f)).hexdigest(),sha)
  inventory=read(DATA/"route-inventory.json")
  bootstrap={v["race_key"]:v for v in read(DATA/"bootstrap.json")["editions"]}
  coverage={v["race_key"]:v for v in read(DATA/"coverage.json")}
  registry=read(ROOT/"config/source-registry.json")["participant_gpx"]["trail43"]
  for year in range(2021,2026):
   key=f"{year}-trail43"
   file=DATA/"routes"/f"{key}-participant.json"
   self.assertTrue(file.is_file(),key)
   route=read(file)
   expected=EARLY if year<=2022 else LATE
   self.assertEqual(route["source_sha256"],expected)
   self.assertEqual(route["original_source_sha256"],SHA[year])
   self.assertEqual(route["edition_references"],[year])
   self.assertGreaterEqual(len(route["points"]),500)
   self.assertEqual(registry[str(year)]["normalized_source_sha256"],expected)
   entries=[v for v in inventory if v.get("race_key")==key and v["type"]=="VERIFIED_PARTICIPANT"]
   self.assertEqual(len(entries),1)
   self.assertEqual(entries[0]["source_sha256"],expected)
   if year<2025:
    self.assertEqual(bootstrap[key]["route_file"],f"routes/{key}-participant.json")
    self.assertEqual(coverage[key]["route_source_type"],"VERIFIED_PARTICIPANT")
   else:
    self.assertEqual(bootstrap[key]["route_file"],"routes/trail43-2025-2026.json")
    self.assertEqual(bootstrap[key]["route_status"],"organizer_2025_2026_reuse_assumption")
  self.assertEqual(len([x for x in inventory if x["type"]=="OFFICIAL_ORGANIZER"]),5)
if __name__=="__main__":unittest.main(verbosity=2)
