#!/usr/bin/env python3
"""Promote one verified race-day participant GPX into a display-only edition route.

This updates only route geometry and its source metadata, never observed EQ Timing
results, stations or splits. It must be run after the ordinary EQ rebuild.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"docs/data"
EARTH_KM=6371.0088

def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def haversine(a,b):
    la1,lo1,la2,lo2=map(math.radians,(a[0],a[1],b[0],b[1]))
    s=math.sin((la2-la1)/2)**2+math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return EARTH_KM*2*math.atan2(math.sqrt(max(0,s)),math.sqrt(max(0,1-s)))

def points_from_gpx(raw):
    root=ET.fromstring(raw)
    pts=[]
    # Suunto's activity "*-route.gpx" exports its genuine recorded sequence
    # as rtept rather than trkpt. Prefer track samples where available;
    # otherwise use that documented Suunto route-point sequence. Never use
    # stand-alone waypoints (wpt) or combine two independent geometries.
    trk=[node for node in root.iter() if node.tag.rsplit("}",1)[-1]=="trkpt"]
    rte=[node for node in root.iter() if node.tag.rsplit("}",1)[-1]=="rtept"]
    source=trk if trk else rte
    for node in source:
        lat=float(node.attrib["lat"]);lon=float(node.attrib["lon"])
        if not (-90<=lat<=90 and -180<=lon<=180):
            raise ValueError("GPX coordinates out of bounds")
        ele=next((child.text for child in node if child.tag.rsplit("}",1)[-1]=="ele"),None)
        height=float(ele) if ele is not None and ele.strip() else None
        p=(lat,lon,height)
        if not pts or haversine(pts[-1],p)>0.000001:
            pts.append(p)
    if len(pts)<100:raise ValueError("Expected >=100 actual recorded trackpoints, found "+str(len(pts)))
    return pts

def simplify(points,tolerance_m=3):
    # Local tangent plane with metre units. Conservative Douglas-Peucker only:
    # raw original is unchanged; no smoothing or editing of excursion geometry.
    latitude=math.radians(sum(x[0] for x in points)/len(points))
    xscale=111195*math.cos(latitude);yscale=111195
    xy=[(p[1]*xscale,p[0]*yscale) for p in points]
    keep={0,len(points)-1};stack=[(0,len(points)-1)];tol2=tolerance_m*tolerance_m
    while stack:
        a,b=stack.pop()
        if b-a<2:continue
        ax,ay=xy[a];bx,by=xy[b];dx=bx-ax;dy=by-ay;d2=dx*dx+dy*dy
        best=tol2;idx=None
        for i in range(a+1,b):
            px,py=xy[i]
            t=max(0,min(1,((px-ax)*dx+(py-ay)*dy)/d2)) if d2 else 0
            distance=(px-ax-t*dx)**2+(py-ay-t*dy)**2
            if distance>best:best=distance;idx=i
        if idx is not None:
            keep.add(idx);stack.extend(((a,idx),(idx,b)))
    return [points[i] for i in sorted(keep)]

def promote(gpx,year,family):
    raw=gpx.read_bytes();original=points_from_gpx(raw)
    expected_ranges={"trail43":(35,51),"trail22":(17,27),"ultra85":(70,100)}
    if family not in expected_ranges:raise ValueError("Unsupported race family")
    original_length=sum(haversine(a,b) for a,b in zip(original,original[1:]))
    lo,hi=expected_ranges[family]
    if not lo<=original_length<=hi:
        raise ValueError(f"{year}/{family}: GPX measured {original_length:.2f} km, expected {lo}–{hi}; manual source inspection required.")
    cleaned=simplify(original)
    chainage=0.;route=[]
    for i,p in enumerate(cleaned):
        if i:chainage+=haversine(cleaned[i-1],p)
        route.append([round(chainage,6),round(p[0],6),round(p[1],6),round(p[2],1) if p[2] is not None else None])
    if len(route)<100:raise ValueError("Over-simplified course; inspect raw source")
    key=f"{year}-{family}"
    catalog_path=DATA/"bootstrap.json";catalog=load(catalog_path)
    edition=next((e for e in catalog["editions"] if e["race_key"]==key),None)
    if not edition:raise ValueError(f"Unknown edition: {key}")
    race_path=DATA/"races"/f"{key}.json";race=load(race_path)
    if race["race_key"]!=key:raise AssertionError("Edition mismatch")
    # No older or newer year's GPX can silently act as a substitute.
    if edition.get("route_file") and edition.get("route_status") not in ("none","participant_track_display_only"):
        raise ValueError(f"Existing independently approved route for {key}: {edition['route_file']}")
    filename=f"{key}-participant.json"
    rel="routes/"+filename
    sha=hashlib.sha256(raw).hexdigest()
    meta={
        "family":family,"edition_references":[year],"race_key":key,
        "type":"VERIFIED_PARTICIPANT",
        "evidence_note":"Recorded participant race-day GPX supplied by project owner; display geometry only. No official checkpoint coordinates, cross-year course equivalence, measured runner GPS positions or timing values are inferred.",
        "source_sha256":sha,"geometry_length_km":round(chainage,6),
        "published_polyline_length_km":round(sum(haversine(a[1:3],b[1:3]) for a,b in zip(route,route[1:])),6),
        "geometry_export_method":"consecutive-deduplication-and-conservative-3m-Douglas-Peucker",
        "raw_source_points":len(original),"published_points":len(route),
        "points":route
    }
    inventory_path=DATA/"route-inventory.json";inventory=load(inventory_path)
    entry={k:v for k,v in meta.items() if k!="points"}|{"source_filename":gpx.name}
    inventory=[item for item in inventory if item.get("race_key")!=key]
    inventory.append(entry)
    inventory.sort(key=lambda row:(row["family"],row["edition_references"][0],row.get("race_key","")))
    updates={
        "route_file":rel,"route_status":"participant_track_display_only",
        "route_source_sha256":sha,
        "measured_route_geometry_km":meta["geometry_length_km"],
        "course_version":f"{key}-participant-display-not-canonical",
    }
    # No edits to race.results, race.splits, or race.stations.
    for obj in (edition,race):obj.update(updates)
    coverage_path=DATA/"coverage.json";coverage=load(coverage_path)
    for obj in coverage:
        if obj["race_key"]==key:
            obj.update(updates)
            obj.update({
                "route_sha256":sha,
                "route_source_type":"VERIFIED_PARTICIPANT",
                "route_source_filename":gpx.name,
                "route_geometry_km":meta["geometry_length_km"],
                "route_evidence_note":meta["evidence_note"],
            })
    registry_path=ROOT/"config/source-registry.json";registry=load(registry_path)
    registry.setdefault("participant_gpx",{}).setdefault(family,{})[str(year)]={
        "status":"VERIFIED_PARTICIPANT","source_sha256":sha,
        "source_file":gpx.as_posix().removeprefix(ROOT.as_posix()+"/"),
        "display_route":rel,"display_only":True
    }
    dump(DATA/rel,meta)
    dump(catalog_path,catalog)
    dump(race_path,race)
    dump(inventory_path,inventory)
    dump(coverage_path,coverage)
    dump(registry_path,registry)
    print(f"PROMOTED {key}: raw points={len(original)}, display={len(route)}, raw km={original_length:.3f}, display km={chainage:.3f}, source SHA256={sha}")
    print("Actual results, timing splits and stations untouched.")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--gpx",type=Path,required=True)
    parser.add_argument("--year",type=int,required=True)
    parser.add_argument("--family",choices=("trail43","trail22","ultra85"),required=True)
    a=parser.parse_args()
    if not a.gpx.is_file():parser.error("Original GPX file not found: "+str(a.gpx))
    promote(a.gpx,a.year,a.family)

if __name__=="__main__":main()
