#!/usr/bin/env python3
"""Restartable import of the owner's checksum-pinned 2021–2025 GPX package.
Run AFTER the package is uploaded to data/source-archive/ on main.
The already approved 2024 year-specific GPX and 2025 organizer GPX remain intact.
"""
from pathlib import Path
import hashlib,json,sys,tempfile,zipfile
ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/"data/source-archive/satila-43km-source-and-normalized-2021-2025.zip"
ORIGINAL={
 2021:("suuntoapp-TrailRunning-2021-11-13T09-00-06Z-route.gpx","d07051fda67d4343ccf9ff49ec7ee8788b923965f14b127e5d7ffaac91a0c9d6"),
 2022:("suuntoapp-Running-2022-11-12T09-00-06Z-route.gpx","b7bd4710327fae74d0478db5dbb1df80c3bb7f84c9d316fd9c2a86028486479c"),
 2023:("suuntoapp-Running-2023-11-11T09-00-01Z-route.gpx","60b5f920d6f4e652db1760120f6d22bd1fcdea722edee46c83dc7d6f0c1e04da"),
 2024:("suuntoapp-Running-2024-11-09T09-00-01Z-route.gpx","d83bfad962e94a69ed0ea53a0c063679478234cccd3a780d714900ae7640c4b4"),
 2025:("suuntoapp-Running-2025-11-08T09-00-05Z-route.gpx","f090e7d461e0ae53e06561c340b1a87bab30f10454e49ebaface2cd19468502b"),
}
NORMAL={
 "trail43-2021-2022-normalized":("e0cf97e943f01d09995b40be2e4c6e6f7a4ca720d991e8ae9416f52fbb43b967",1090,44.30917),
 "trail43-2023-2025-normalized":("bb46f69cd304451b3caca315e80936ded07e0c5b18d0333b63f262ecec13e15c",822,41.873734),
}
def digest(blob):return hashlib.sha256(blob).hexdigest()
def main():
 if not PACKAGE.is_file():raise SystemExit("Upload missing package: "+str(PACKAGE))
 if digest(PACKAGE.read_bytes())!="3427a19a066abdef1b1c60dcb37a67015781af406dbf0988c32e1e63a451828c":
  raise SystemExit("Package SHA256 mismatch; refuse any publication")
 with zipfile.ZipFile(PACKAGE) as z:
  if z.testzip() is not None:raise SystemExit("Damaged source package")
  for year,(name,sha) in ORIGINAL.items():
   raw=z.read("original/"+name)
   assert digest(raw)==sha,(year,"original SHA mismatch")
  for key,(compressed_sha,npoints,km) in NORMAL.items():
   encoded=z.read("normalized/"+key+".route64")
   assert digest(encoded)==compressed_sha,(key,"encoded route mismatch")
   obj=json.loads(z.read("normalized/"+key+".json"))
   assert len(obj["points"])==npoints,(key,"point count mismatch")
   assert abs(obj["geometry_length_km"]-km)<.00001,(key,"normalized distance mismatch")
  from tempfile import TemporaryDirectory
  import sys
  sys.path.insert(0,str(ROOT/"tools"))
  from promote_participant_gpx import promote
  with TemporaryDirectory() as td:
   work=Path(td)
   for year,key in ((2021,"trail43-2021-2022-normalized"),(2022,"trail43-2021-2022-normalized"),(2023,"trail43-2023-2025-normalized")):
    gpx=work/(key+".gpx")
    gpx.write_bytes(z.read("normalized/"+key+".gpx"))
    promote(gpx,year,"trail43")
    # The source is archived inside the durable ZIP, not at the transient runner path.
    registry_file=ROOT/"config/source-registry.json"
    registry=json.loads(registry_file.read_text(encoding="utf-8"))
    registry["participant_gpx"]["trail43"][str(year)]["source_file"]=str(PACKAGE.relative_to(ROOT))+"#normalized/"+key+".gpx"
    registry_file.write_text(json.dumps(registry,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
  # The 2024 same-corridor source is already published and checksum locked;
  # 2025 official organizer route is retained, never silently replaced.
  boot=json.loads((ROOT/"docs/data/bootstrap.json").read_text())
  mapped={e["year"]:e.get("route_file") for e in boot["editions"] if e["family"]=="trail43"}
  for y in range(2021,2026):
   assert mapped[y],("missing owner-accepted route",y)
  print("SUCCESS: all five original GPX hashes checked; both reconstructed families verified; 2021–2025 all have a year-authorized map")
if __name__=="__main__":main()
