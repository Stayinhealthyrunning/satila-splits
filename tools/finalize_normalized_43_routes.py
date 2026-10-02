#!/usr/bin/env python3
"""Finalize already committed owner-accepted 43 km maps without changing EQ Timing rows."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"docs"/"data"
LINKS={2021:("trail43-2021-2022","813ae56de63aaff3dbbcb464f2f10105a190c54525e3623953393980c21c5523"),
       2022:("trail43-2021-2022","813ae56de63aaff3dbbcb464f2f10105a190c54525e3623953393980c21c5523"),
       2023:("trail43-2023-2025","26c071f709fab6d00907c630af9ab5ba874415d96a788db9c541ba5839e63487")}

def read(path): return json.loads(path.read_text(encoding="utf-8"))
def write(path,value): path.write_text(json.dumps(value,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")

bootstrap=read(DATA/"bootstrap.json")
coverage_path=DATA/"coverage.json";coverage=read(coverage_path)
registry_path=ROOT/"config/source-registry.json";registry=read(registry_path)
inventory=read(DATA/"route-inventory.json")
for year,(group,expected) in LINKS.items():
    key=f"{year}-trail43"
    archive=ROOT/"data/source-archive"/f"{group}-normalized.json"
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    assert digest==expected,(key,digest,expected)
    original=read(archive)
    assert original["family"]=="trail43" and year in original["edition_references"]
    assert len(original["points"])>=800
    ed=next(e for e in bootstrap["editions"] if e["race_key"]==key)
    route=DATA/"routes"/f"{key}-participant.json"
    assert ed["route_file"]=="routes/"+route.name and route.is_file()
    obj=read(route)
    assert obj["type"]=="VERIFIED_PARTICIPANT"
    assert obj["edition_references"]==[year] and obj["race_key"]==key
    assert obj["source_sha256"]==digest and obj["points"]==original["points"]
    assert len([x for x in inventory if x.get("race_key")==key])==1
    race=read(DATA/"races"/f"{key}.json")
    for prop in ("route_file","route_status","route_source_sha256","measured_route_geometry_km","course_version"):
        assert race[prop]==ed[prop],(key,prop)
    cov=next(x for x in coverage if x["race_key"]==key)
    for prop in ("route_file","route_status","route_source_sha256","measured_route_geometry_km","course_version"):
        cov[prop]=ed[prop]
    cov.update(route_sha256=digest,route_source_type="VERIFIED_PARTICIPANT",
               route_source_filename=f"{group}-normalized.json",
               route_geometry_km=original["geometry_length_km"],
               route_evidence_note=obj["evidence_note"])
    registry.setdefault("participant_gpx",{}).setdefault("trail43",{})[str(year)]={
        "status":"VERIFIED_PARTICIPANT","route_processing":"OWNER_ACCEPTED_NORMALIZED",
        "source_sha256":digest,
        "original_source_sha256":original["source_original_sha256"][str(year)],
        "source_file":f"data/source-archive/{group}-normalized.json",
        "display_route":f"routes/{key}-participant.json","display_only":True}
    print("LINKED",key,group,len(original["points"]),original["geometry_length_km"],digest)
# The original year-specific 2024 track and 2025 organizer GPX remain intact.
for year in (2024,2025):
    ed=next(e for e in bootstrap["editions"] if e["race_key"]==f"{year}-trail43")
    assert ed.get("route_file") and (DATA/ed["route_file"]).is_file()
write(coverage_path,coverage)
write(registry_path,registry)
assert sum(bool(x.get("route_file")) for x in bootstrap["editions"] if x["family"]=="trail43" and x["year"] in (2021,2022,2023,2024,2025))==5
print("PASS 43 km 2021–2025: five map-enabled editions; 2024/2025 original published sources preserved")
