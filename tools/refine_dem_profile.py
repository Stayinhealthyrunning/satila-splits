#!/usr/bin/env python3
"""Produce explicitly labelled, robustly smoothed historical Copernicus DSM profiles.

Research filter selected by actual same-coordinate 2026 organizer 85 km and
43 km GPX tests. Spatial median radius 50 m followed by Gaussian sigma 60 m.
Distance-based windows, not a fixed number of GPX points. Historic participant
geometry, original source SHA-256, split timings and station anchors unchanged.
This is approximate DSM SURFACE height, not surveyed bare-earth terrain or D+.
"""
from __future__ import annotations
import argparse,bisect,json,math,statistics
from pathlib import Path

def smooth_route(route:dict,median_radius_m:float=50.,sigma_m:float=60.) -> dict:
    pts=route["points"]
    if len(pts)<2 or median_radius_m<=0 or sigma_m<20:
        raise ValueError("Invalid route or smoothing parameters")
    if any(not isinstance(p[3],(float,int)) or not math.isfinite(p[3]) for p in pts):
        raise ValueError("Incomplete input candidate elevations")
    km=[float(p[0]) for p in pts]
    hs=[float(p[3]) for p in pts]
    if any(b<=a for a,b in zip(km,km[1:])):
        raise ValueError("Distances must be strictly increasing")
    # Identical to the selected parameter combination in evaluate_dem_smoothing.py
    med=[]
    radius=median_radius_m/1000
    for i,d in enumerate(km):
        a=bisect.bisect_left(km,d-radius)
        b=bisect.bisect_right(km,d+radius)
        med.append(statistics.median(hs[a:b]))
    sigma=sigma_m/1000
    smoothed=[]
    for i,d in enumerate(km):
        a=bisect.bisect_left(km,d-3*sigma)
        b=bisect.bisect_right(km,d+3*sigma)
        weighted=[(math.exp(-.5*((km[j]-d)/sigma)**2),med[j]) for j in range(a,b)]
        smoothed.append(sum(w*v for w,v in weighted)/sum(w for w,_ in weighted))
    out=dict(route)
    out["points"]=[[p[0],p[1],p[2],round(v,2)] for p,v in zip(pts,smoothed)]
    pv=dict(out["elevation_provenance"])
    pv["type"]="DSM_RECONSTRUCTED_SURFACE"
    pv["filter"]="symmetric-distance-median-50m-then-Gaussian-sigma-60m"
    pv["surface_not_ground"]=True
    pv["not_official_ascent_or_runner_altitude"]=True
    pv["model"]="Copernicus DEM GLO-30 Public (2021), digital surface model, nominal 30m"
    pv["source_notice"]="produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved"
    pv["legal_notice"]="The organisations in charge of the Copernicus programme by law or by delegation do not incur any liability for any use of the Copernicus WorldDEM-30."
    out["elevation_provenance"]=pv
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input-dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    args=p.parse_args()
    paths=sorted(args.input_dir.glob("*-ultra85-participant.json"))
    if len(paths)!=7:raise SystemExit("Expected seven candidate JSON routes")
    args.output_dir.mkdir(parents=True,exist_ok=True)
    for path in paths:
        result=smooth_route(json.loads(path.read_text()))
        target=args.output_dir/path.name
        if target.exists():raise FileExistsError(target)
        target.write_text(json.dumps(result,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf8")
        values=[p[3] for p in result["points"]]
        print(path.name,len(values),"filtered min",min(values),"max",max(values),flush=True)

if __name__=="__main__":main()
