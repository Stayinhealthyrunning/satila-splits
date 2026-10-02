#!/usr/bin/env python3
"""Smooth preliminary DSM surface profiles along *route distance* without changing route geometry.

Copernicus GLO-30 Public is a DSM with vegetation/buildings; use heights only as
approximate reconstructed surface elevations, never source GPX heights or official D+.
Distance-weighted Gaussian convolution on a uniform 20m sample grid prevents
non-uniform race-day participant GPS sample density changing filtering strength.
"""
from __future__ import annotations
import argparse,bisect,json,math
from pathlib import Path

def smooth_route(route:dict, sigma_m:float=65., interval_m:float=20.) -> dict:
    pts=route["points"]
    if len(pts)<2 or sigma_m<20 or interval_m>sigma_m:
        raise ValueError("Invalid route or smoothing parameters")
    if any(not isinstance(p[3],(float,int)) or not math.isfinite(p[3]) for p in pts):
        raise ValueError("Incomplete input candidate elevations")
    kms=[float(p[0]) for p in pts]
    hs=[float(p[3]) for p in pts]
    if any(b<=a for a,b in zip(kms,kms[1:])):
        raise ValueError("Distances must be strictly increasing")
    grid=[]
    step=interval_m/1000.
    n=math.ceil((kms[-1]-kms[0])/step)
    for i in range(n+1):
        km=min(kms[-1],kms[0]+i*step)
        idx=min(len(kms)-2,max(0,bisect.bisect_right(kms,km)-1))
        ratio=(km-kms[idx])/(kms[idx+1]-kms[idx])
        h=hs[idx]+ratio*(hs[idx+1]-hs[idx])
        grid.append((km,h))
    if grid[-1][0]<kms[-1]:
        grid.append((kms[-1],hs[-1]))
    gs=[x[0] for x in grid]
    vals=[x[1] for x in grid]
    radius=3*sigma_m/1000.
    result=[]
    for point in pts:
        km=point[0]
        low=bisect.bisect_left(gs,km-radius)
        high=bisect.bisect_right(gs,km+radius)
        numerator=denominator=0.
        for j in range(low,high):
            d_m=(gs[j]-km)*1000
            w=math.exp(-.5*(d_m/sigma_m)**2)
            numerator+=vals[j]*w;denominator+=w
        result.append([point[0],point[1],point[2],round(numerator/denominator,2)])
    out=dict(route)
    out["points"]=result
    pv=dict(out["elevation_provenance"])
    pv["type"]="DSM_RECONSTRUCTED_SURFACE"
    pv["filter"]="uniform-distance-resampling-20m-and-Gaussian-sigma-65m"
    pv["surface_not_ground"]=True
    pv["not_official_ascent_or_runner_altitude"]=True
    pv["model"]="Copernicus DEM GLO-30 Public (2021), digital surface model, nominal 30m"
    pv["source_notice"]="produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved"
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
