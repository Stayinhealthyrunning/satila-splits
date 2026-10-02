#!/usr/bin/env python3
"""Checksum-locked geometry integrity test for organizer display routes.

Avoids confusing the GPS display axis with the timing/results axis.
No participant identities, raw GPX, or guessed positions are needed.
"""
from __future__ import annotations
import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from build_satila import build_route_asset_from_trackpoints

ROOT=Path(__file__).resolve().parents[1]/"docs"/"data"
CHECKSUMS={
 "trail5":"304fe04cba9ae22840253a99589fe142c31971ee129cc3fb38dde0ecfbc7144d",
 "trail10":"24fc6f0ff6eca90dade4471e4743dccbed2272c02fe88b6619c46c6ece9d7c91",
 "trail22":"c78872ddd3d9e0575eb260227a2d9b40455d7841d0d8a4dcfe71614356a06c39",
 "trail43":"4b10bee2201e8f2493a1bf564c1603c5431c123fdc8d19dfb432655fb04ee827",
 "ultra85":"c5c313faf2b137cfeacf3b90cee4638094070793d70c8a88ca00944360f582c0",
}

def geo(a,b):
    lat1,lon1,lat2,lon2=map(math.radians,[a[1],a[2],b[1],b[2]])
    v=math.sin((lat2-lat1)/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return 6371.0088*2*math.atan2(math.sqrt(max(0,v)),math.sqrt(max(0,1-v)))

def main():
    inventory=json.loads((ROOT/"route-inventory.json").read_text(encoding="utf-8"))
    organizer=[x for x in inventory if x.get("type")=="OFFICIAL_ORGANIZER"]
    participant=[x for x in inventory if x.get("type") in ("VERIFIED_PARTICIPANT","TRACE_DE_TRAIL")]
    assert len(organizer)==len(CHECKSUMS)
    assert {x["family"] for x in organizer}==set(CHECKSUMS)
    assert len(organizer)+len(participant)==len(inventory)
    total_bytes=0
    for route in organizer:
        family=route["family"]
        assert route["source_sha256"]==CHECKSUMS[family],f"{family}: raw provenance checksum changed"
        assert route.get("type")=="OFFICIAL_ORGANIZER"
        refs=[2026] if family=="ultra85" else [2025,2026]
        assert route["edition_references"]==refs, f"{family}: incorrect year reuse metadata"
        file=ROOT/"routes"/(f"{family}-2025-2026.json" if family!="ultra85" else "ultra85-2026.json")
        assert file.exists(),f"{family}: missing route asset"
        item=json.loads(file.read_text(encoding="utf-8"))
        assert item["source_sha256"]==route["source_sha256"]
        assert item["edition_references"]==refs
        assert item["family"]==family
        pts=item["points"]
        assert len(pts)>=10
        assert all(len(p)==4 for p in pts)
        assert abs(pts[0][0])<=0.001
        assert abs(pts[-1][0]-route["geometry_length_km"])<=0.002
        assert item.get("geometry_export_method")=="all_geometrically_unique_source_trackpoints"
        assert route.get("published_points")==len(pts)
        assert len(pts)>=route["source_points"]*.98,f"{family}: source geometry was unexpectedly discarded"
        file_bytes=file.stat().st_size
        total_bytes+=file_bytes
        assert file_bytes<=256_000,f"{family}: individual route asset exceeds 256 kB"
        assert not any("time" in str(x).lower() for x in item.keys()),"No invented timestamps in display routes"
        for prev,current in zip(pts,pts[1:]):
            for p in (prev,current):
                d,lat,lon,ele=p
                assert math.isfinite(d) and d>=0
                assert 56<=lat<=59 and 11<=lon<=14,f"{family}: coordinate outside expected geographic envelope"
                assert ele is None or math.isfinite(ele)
            assert current[0]>prev[0],f"{family}: non-monotone or duplicated cumulative distance"
            direct=geo(prev,current)
            recorded=current[0]-prev[0]
            assert direct<=recorded+.035,f"{family}: impossible point-to-point distance in sampled path"
        drawn=sum(geo(a,b) for a,b in zip(pts,pts[1:]))
        retention=drawn/item["geometry_length_km"]
        assert retention>=.998,f"{family}: rendered polyline retains only {retention:.3%} of source length"
        assert abs(drawn-item["published_polyline_length_km"])<=.002
        print(f"PASS {family}: {len(pts)} source-faithful display points, {drawn:.3f}/{item['geometry_length_km']:.3f} km ({retention:.3%}), {file_bytes} bytes, official source sha256 {item['source_sha256'][:12]}…")
    assert total_bytes<=512_000,f"Official route assets exceed 512 kB raw: {total_bytes}"
    for route in participant:
        key=route["race_key"];year=int(key.split("-",1)[0])
        assert route["edition_references"]==[year],f"{key}: GPX must only apply to its own year"
        asset=ROOT/"routes"/f"{key}-participant.json"
        assert asset.is_file(),f"{key}: missing display route"
        obj=json.loads(asset.read_text(encoding="utf-8"))
        assert obj["source_sha256"]==route["source_sha256"]
        assert obj["race_key"]==key and obj["edition_references"]==[year]
        points=obj["points"]
        assert len(points)>=100 and len(points)==route["published_points"]
        assert all(len(p)==4 and 56<=p[1]<=59 and 11<=p[2]<=14 and
                   (p[3] is None or math.isfinite(p[3])) for p in points)
        assert abs(points[0][0])<.001
        assert all(cur[0]>prev[0] for prev,cur in zip(points,points[1:]))
        assert abs(points[-1][0]-route["geometry_length_km"])<.002
        assert not any(k in obj for k in ("raw_gpx","participant_name","timestamps"))
        print(f"PASS {key}: {len(points)} GPX display points with year-locked source")

    # A tight synthetic switchback verifies the exporter itself rather than only
    # the already generated assets. Every real bend must survive publication.
    coordinates=[(57.0000,12.0000,100),(57.0000,12.0005,100),(57.0003,12.0005,100),
                 (57.0003,12.0001,100),(57.0006,12.0001,100),(57.0006,12.0006,100)]
    asset,meta=build_route_asset_from_trackpoints(coordinates,"trail43",b"synthetic fixture","synthetic.gpx")
    assert len(asset["points"])==len(coordinates)==meta["published_points"]
    synthetic_drawn=sum(geo(a,b) for a,b in zip(asset["points"],asset["points"][1:]))
    assert synthetic_drawn/asset["points"][-1][0]>=.998
    assert asset["points"][2][1:3]==[57.0003,12.0005]
    assert asset["points"][3][1:3]==[57.0003,12.0001]
    print("PASS synthetic tight-turn route preserves every source bend")
    print("ALL FIVE CHECKSUM-LOCKED DISPLAY ROUTES PASSED")

if __name__=="__main__":
    main()
