#!/usr/bin/env python3
"""Deterministic physical-distance smoothing experiment for Copernicus DSM.

The 30 m Copernicus GLO-30 is a SURFACE model. Median removes isolated pixels,
Gaussian low-pass prevents exaggerated raw ascent when sampled along a path.
Parameter study is benchmarked against observed heights in independent GPXs
at precisely matching geographic positions, not against their course progress.
No timing fields are used; raw altitude/D+ is never passed off as official.
"""
import argparse
import bisect
import json
import math
import statistics
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_dem_candidates import percentile, hills
from enrich_route_elevation import GeoTiffSampler

def filter_heights(pts, median_radius_m=0, gaussian_sigma_m=0):
    km=[p[0] for p in pts]
    raw=[float(p[3]) for p in pts]
    # Distances are in km; use a spatially symmetric window rather than
    # fixed number of GPX vertices (sampling densities differ across years).
    med=[]
    mr=median_radius_m/1000
    for i,x in enumerate(km):
        a=bisect.bisect_left(km,x-mr)
        b=bisect.bisect_right(km,x+mr)
        med.append(statistics.median(raw[a:b]))
    sigma=gaussian_sigma_m/1000
    if sigma==0:
        smoothed=med
    else:
        smoothed=[]
        radius=3*sigma
        for i,x in enumerate(km):
            a=bisect.bisect_left(km,x-radius)
            b=bisect.bisect_right(km,x+radius)
            weighted=[(math.exp(-.5*((km[j]-x)/sigma)**2),med[j]) for j in range(a,b)]
            smoothed.append(sum(w*v for w,v in weighted)/sum(w for w,_ in weighted))
    return smoothed

def step_audit(pts, vals):
    delta=[(abs(b-a),(pts[i+1][0]-pts[i][0])*1000) for i,(a,b) in enumerate(zip(vals,vals[1:]))]
    short=[dz for dz,horiz in delta if 0<horiz<=100]
    return {"p95_step_m":round(percentile(short,.95),2),"max_step_m":round(max(short),2),"steps_over_20m":sum(z>20 for z in short)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--dem",type=Path,required=True)
    ap.add_argument("--candidate-dir",type=Path,required=True)
    ap.add_argument("--reference",type=Path,nargs="+",required=True)
    ap.add_argument("--report",type=Path,required=True)
    args=ap.parse_args()
    params=[(0,0),(50,60),(75,90),(100,120),(125,150),(150,200),(200,250)]
    histories=[json.loads(p.read_text()) for p in sorted(args.candidate_dir.glob("*-ultra85-participant.json"))]
    assert len(histories)==7
    refs=[]
    with GeoTiffSampler([args.dem]) as sampler:
        for p in args.reference:
            source=json.loads(p.read_text())
            sampled=[]
            for point in source["points"]:
                km,lat,lon,h=point
                value=sampler(lat,lon)
                if isinstance(h,(int,float)) and value is not None:
                    sampled.append([km,lat,lon,value,float(h)])
            assert len(sampled)>500,p
            refs.append((p.name,sampled))
    report=[]
    for mr,gs in params:
        out={"median_radius_m":mr,"gaussian_sigma_m":gs,"reference":[],"candidate":[]}
        for name,points in refs:
            vals=filter_heights([p[:4] for p in points],mr,gs)
            diffs=[v-p[4] for v,p in zip(vals,points)]
            median=statistics.median(diffs)
            centered=[abs(d-median) for d in diffs]
            dsm_profile=[[p[0],p[1],p[2],v] for p,v in zip(points,vals)]
            source_profile=[[p[0],p[1],p[2],p[4]] for p in points]
            gain_dsm=hills(dsm_profile);gain_reference=hills(source_profile)
            out["reference"].append({
                "name":name,"n":len(diffs),
                "median_offset_m":round(median,2),
                "absolute_residual_p90_m":round(percentile([abs(v) for v in diffs],.9),2),
                "centered_abs_residual_p90_m":round(percentile(centered,.9),2),
                "reconstructed_gain_100m_m":gain_dsm,
                "source_gain_100m_m":gain_reference,
                "gain_ratio":round(gain_dsm/gain_reference,3),
                **step_audit([p[:4] for p in points],vals),
            })
        for r in histories:
            pts=r["points"];val=filter_heights(pts,mr,gs)
            filtered=[[d,lat,lon,v] for (d,lat,lon,_),v in zip(pts,val)]
            out["candidate"].append({
                "year":r["edition_references"][0],
                "gain_100m_m":hills(filtered),
                "min_m":round(min(val),2),
                "max_m":round(max(val),2),
                **step_audit(pts,val),
            })
        report.append(out)
        print("FILTER",mr,gs,"REF",json.dumps(out["reference"]),"HIST",json.dumps(out["candidate"]),flush=True)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("RESULTS",args.report)

if __name__=="__main__":
    main()
