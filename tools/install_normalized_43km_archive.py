#!/usr/bin/env python3
"""Install owner-approved, reconstructed 2021–2025 Sätila 43 km GPX display routes.

The single public source ZIP contains five original owner activity exports and
two normalized, metadata-free GPX.  All seven hashes are pinned here. Race
results, observed splits and station metadata must not be changed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"docs"/"data"
ARCHIVE=ROOT/"data"/"participant-gpx"/"satila-43km-2021-2025-source-and-normalized.zip"
ORIGINALS={
 2021:("suuntoapp-TrailRunning-2021-11-13T09-00-06Z-route.gpx","d07051fda67d4343ccf9ff49ec7ee8788b923965f14b127e5d7ffaac91a0c9d6"),
 2022:("suuntoapp-Running-2022-11-12T09-00-06Z-route.gpx","b7bd4710327fae74d0478db5dbb1df80c3bb7f84c9d316fd9c2a86028486479c"),
 2023:("suuntoapp-Running-2023-11-11T09-00-01Z-route.gpx","60b5f920d6f4e652db1760120f6d22bd1fcdea722edee46c83dc7d6f0c1e04da"),
 2024:("suuntoapp-Running-2024-11-09T09-00-01Z-route.gpx","d83bfad962e94a69ed0ea53a0c063679478234cccd3a780d714900ae7640c4b4"),
 2025:("suuntoapp-Running-2025-11-08T09-00-05Z-route.gpx","f090e7d461e0ae53e06561c340b1a87bab30f10454e49ebaface2cd19468502b")
}
GROUPS={
 "trail43-2021-2022":("Satila_Trail_43km_2021-2022_NORMALISERAD.gpx","a41883b1157314a6a101a74bf2627f05dfb0ba9cbf24257571b3c8fd9a592f75",(2021,2022)),
 "trail43-2023-2025":("Satila_Trail_43km_2023-2025_NORMALISERAD.gpx","90abb0279946528af88e807057e6000163b423583363a0d7739b19ae61165d80",(2023,2024,2025))
}
EARTH_KM=6371.0088
def digest(raw):return hashlib.sha256(raw).hexdigest()
def read(path):return json.loads(path.read_text(encoding="utf-8"))
def dump(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(obj,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
def km(a,b):
 a1,o1,a2,o2=map(math.radians,(a[0],a[1],b[0],b[1]))
 v=math.sin((a2-a1)/2)**2+math.cos(a1)*math.cos(a2)*math.sin((o2-o1)/2)**2
 return 2*EARTH_KM*math.asin(min(1,math.sqrt(max(0,v))))
def geometry(raw):
 root=ET.fromstring(raw)
 # Only the normalized track samples are exported; never GPX author/activity metadata.
 nodes=root.findall(".//{*}trkpt")
 if not nodes:raise ValueError("Missing normalized GPX track points")
 out=[];distance=0.
 for node in nodes:
  lat,lon=float(node.attrib["lat"]),float(node.attrib["lon"])
  if not 56<lat<59 or not 11<lon<14:raise ValueError("GPX coordinates outside Sätila area")
  el=node.find("{*}ele");height=float(el.text) if el is not None and el.text else None
  if out:
   step=km((out[-1][1],out[-1][2]),(lat,lon))
   if step<=.000001:continue
   distance+=step
  out.append([round(distance,6),round(lat,6),round(lon,6),round(height,1) if height is not None else None])
 if len(out)<500 or not 40<distance<47:raise ValueError("Unexpected normalized route geometry")
 if any(b[0]<=a[0] for a,b in zip(out,out[1:])):raise ValueError("Non-monotone route chainage")
 return out,round(distance,6)

def install(archive):
 with ZipFile(archive) as z:
  expected={"SOURCE_MANIFEST.json"}|{"original/"+name for name,_ in ORIGINALS.values()}|{"normalized/"+name for name,_,_ in GROUPS.values()}
  if set(z.namelist())!=expected:raise ValueError("Archive content differs from exactly five originals, two normalized routes and manifest")
  if z.testzip():raise ValueError("Archive CRC check failed")
  manifest=json.loads(z.read("SOURCE_MANIFEST.json"))
  for year,(filename,sha) in ORIGINALS.items():
   member="original/"+filename;raw=z.read(member)
   if digest(raw)!=sha or manifest["originals"][str(year)]["sha256"]!=sha:raise ValueError("Original changed: "+str(year))
  normalized={}
  for group,(filename,sha,years) in GROUPS.items():
   raw=z.read("normalized/"+filename)
   if digest(raw)!=sha or manifest["normalized"][group]["sha256"]!=sha:raise ValueError("Normalized route changed: "+group)
   pts,length=geometry(raw)
   normalized[group]={"points":pts,"length":length,"sha":sha,"filename":filename,"years":years}
 catalog_path=SITE/"bootstrap.json";catalog=read(catalog_path)
 inventory_path=SITE/"route-inventory.json";inventory=read(inventory_path)
 coverage_path=SITE/"coverage.json";coverage=read(coverage_path)
 registry_path=ROOT/"config"/"source-registry.json";registry=read(registry_path)
 versions_path=ROOT/"config"/"course-versions.json";versions=read(versions_path)
 editions={e["race_key"]:e for e in catalog["editions"]}
 coverage_by_key={e["race_key"]:e for e in coverage}
 if len(editions)!=27:raise ValueError("Expected immutable 27 historical editions")
 selected={f"{year}-trail43" for year in range(2021,2026)}
 inventory=[item for item in inventory if item.get("race_key") not in selected]
 archive_rel=archive.relative_to(ROOT).as_posix()
 for group,record in normalized.items():
  years=record["years"]
  candidate=versions["normalized_route_candidates"][group]
  if candidate.get("sha256")!=record["sha"]:
   candidate.setdefault("historical_unrecovered_file_sha256",candidate.get("sha256"))
  candidate.update({
   "filename":record["filename"],"sha256":record["sha"],
   "point_count":len(record["points"]),"geometry_length_km":record["length"],
   "status":"OWNER_ACCEPTED_FOR_YEAR_SCOPED_DISPLAY",
   "rebuild_note":"2026-10-02 reproducible reconstruction from five original GPX; not byte-identical to unrecovered September normalized GPX."
  })
  for year in years:
   key=f"{year}-trail43";rel=f"routes/{key}-participant.json"
   original_filename,original_sha=ORIGINALS[year]
   evidence=("Owner-approved participant-normalized course corridor "+group+
     "; display geometry only. Original race-day GPS sha256 "+original_sha+
     "; no GPS timestamps, invented checkpoint observations, official course assertion or cross-year timing equivalence.")
   route={
    "family":"trail43","edition_references":[year],"race_key":key,
    "type":"VERIFIED_PARTICIPANT","evidence_note":evidence,
    "source_sha256":record["sha"],"original_source_sha256":original_sha,
    "normalized_course_group":group,"geometry_length_km":record["length"],
    "published_polyline_length_km":record["length"],
    "geometry_export_method":"owner-approved corrected / three-track medoid consensus; reconstructed 2026-10-02",
    "raw_source_points":manifest["originals"][str(year)]["points"],
    "published_points":len(record["points"]),"points":record["points"]
   }
   dump(SITE/rel,route)
   inventory.append({k:v for k,v in route.items() if k!="points"}|{"source_filename":record["filename"]})
   registry.setdefault("participant_gpx",{}).setdefault("trail43",{})[str(year)]={
    "status":"VERIFIED_PARTICIPANT","source_sha256":original_sha,
    "source_file":archive_rel+"#original/"+original_filename,
    "normalized_source_sha256":record["sha"],
    "normalized_source_file":archive_rel+"#normalized/"+record["filename"],
    "normalized_course_group":group,"display_route":rel,"display_only":True
   }
   versions["year_candidates"][str(year)].update({"status":"OWNER_ACCEPTED_FOR_YEAR_SCOPED_DISPLAY","display_route":rel})
   # 2025 organizer GPX remains the preferred primary map. Its 2025/26
   # reuse is a separately documented source; normalized 2025 is retained
   # as additional independent accepted evidence.
   if year==2025:continue
   race_path=SITE/"races"/(key+".json");race=read(race_path)
   source_before={key:race[key] for key in ("results","splits","stations")}
   changes={
    "route_file":rel,"route_status":"participant_track_display_only",
    "route_source_sha256":record["sha"],
    "measured_route_geometry_km":record["length"],
    "course_version":group+"-participant-normalized-display-only"
   }
   editions[key].update(changes);race.update(changes)
   for immutable,value in source_before.items():
    if race[immutable]!=value:raise AssertionError("Timing results or observations changed")
   dump(race_path,race)
   row=coverage_by_key[key];row.update(changes)
   row.update({"route_sha256":record["sha"],"route_source_type":"VERIFIED_PARTICIPANT",
    "route_source_filename":record["filename"],"route_geometry_km":record["length"],"route_evidence_note":evidence})
 inventory.sort(key=lambda e:(e["family"],e["edition_references"][0],e.get("race_key","")))
 registry["privacy_rule"]="Owner has explicitly approved archiving their five original participant GPX publicly. Only metadata-free geometry is deployed under docs."
 dump(catalog_path,catalog);dump(inventory_path,inventory);dump(coverage_path,coverage)
 dump(registry_path,registry);dump(versions_path,versions)
 print("PASS: all five original and both normalized GPX SHA-256 hashes verified")
 print("PASS: 2021–2024 use owner-accepted normalized course; 2025 retains original organizer as preferred map plus normalized alternative")
 print("PASS: EQ Timing results, observed splits and station metadata unchanged")

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument("--archive",type=Path,default=ARCHIVE)
 args=parser.parse_args()
 if not args.archive.is_file():parser.error("Source archive not uploaded: "+str(args.archive))
 install(args.archive.resolve())
if __name__=="__main__":main()
