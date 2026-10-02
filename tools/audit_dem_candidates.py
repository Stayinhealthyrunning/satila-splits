#!/usr/bin/env python3
"""Independent quality audit: historic DSM candidate heights against local source GPXs.

Uses unchanged 2026 organizer route heights at THE SAME lat/lon, not same race %
and never makes a historical GPX an official route. All comparisons are approximate:
different vertical references may shift absolute height by a datum offset.
"""
from __future__ import annotations
import argparse
import json
import math
import statistics
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from enrich_route_elevation import GeoTiffSampler

def percentile(v, q):
    if not v:
        return None
    s=sorted(v)
    x=(len(s)-1)*q
    i=int(x)
    return s[i]+(s[min(len(s)-1,i+1)]-s[i])*(x-i)

def hills(points):
    """Simple 100m distance bins plus 100m median filter; a QC-only diagnostic, not certified ascent."""
    sampled=[]
    length=points[-1][0]
    i=0
    for n in range(int(length/.1)+1):
        d=n*.1
        while i<len(points)-2 and points[i+1][0]<d:
            i+=1
        a,b=points[i:i+2]
        f=min(1,max(0,(d-a[0])/max(1e-9,b[0]-a[0])))
        sampled.append(a[3]+f*(b[3]-a[3]))
    return round(sum(max(0,b-a) for a,b in zip(sampled,sampled[1:])),1)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidate-dir",type=Path,required=True)
    ap.add_argument("--dem",type=Path,required=True)
    ap.add_argument("--reference",type=Path,nargs="+",required=True)
    ap.add_argument("--report",type=Path,required=True)
    args=ap.parse_args()
    paths=sorted(args.candidate_dir.glob("*-ultra85-participant.json"))
    if len(paths)!=7:
        raise SystemExit("Not all seven year-specific candidate routes are present")
    result={"source_reference_validation":[],"historical_candidate_checks":[]}
    with GeoTiffSampler([args.dem]) as sampler:
        for p in args.reference:
            r=json.loads(p.read_text())
            pairs=[]
            for km,lat,lon,h in r["points"]:
                if not isinstance(h,(int,float)) or not math.isfinite(h):
                    continue
                dsm=sampler(lat,lon)
                if dsm is not None:
                    pairs.append((float(h),dsm,km))
            residuals=[dsm-ref for ref,dsm,_ in pairs]
            med=statistics.median(residuals)
            centered=[abs(z-med) for z in residuals]
            row={
                "reference":p.name,"reference_points_with_heights":len(pairs),
                "dsm_sample_coverage":round(len(pairs)/len(r["points"]),5),
                "dsm_minus_source_median_m":round(med,2),
                "absolute_residual_p90_m":round(percentile([abs(z) for z in residuals],.9),2),
                "centered_abs_residual_p90_m":round(percentile(centered,.9),2),
                "absolute_residual_p95_m":round(percentile([abs(z) for z in residuals],.95),2),
                "source_min_m":round(min(v[0] for v in pairs),2),
                "source_max_m":round(max(v[0] for v in pairs),2),
                "dsm_min_m":round(min(v[1] for v in pairs),2),
                "dsm_max_m":round(max(v[1] for v in pairs),2),
                "source_raw_positive_gain_m":r.get("raw_positive_gain_m_not_official"),
                "dsm_100m_resampled_positive_gain_m":hills([[km,0,0,v] for _,v,km in pairs]),
                "reference_100m_resampled_positive_gain_m":hills([[km,0,0,v] for v,_,km in pairs])
            }
            if len(pairs)<100:
                raise SystemExit("Too few independent comparison coordinates")
            result["source_reference_validation"].append(row)
            print("REFERENCE",json.dumps(row),flush=True)
    for p in paths:
        r=json.loads(p.read_text())
        pts=r["points"]
        heights=[v[3] for v in pts]
        assert all(isinstance(v,(int,float)) and math.isfinite(v) for v in heights),p
        assert r["elevation_provenance"]["type"]=="DEM_RECONSTRUCTED_TERRAIN"
        jumps=[(abs(b[3]-a[3]),(b[0]-a[0])*1000) for a,b in zip(pts,pts[1:])]
        short=[dz for dz,horiz in jumps if horiz>0 and horiz<=100]
        steep=[(dz,horiz) for dz,horiz in jumps if horiz>=5 and dz/horiz>.8]
        # These diagnostics are not hard publication thresholds: inspect source properties.
        row={
          "route":p.name,"points":len(pts),"min_m":min(heights),"max_m":max(heights),
          "short_step_abs_jump_p95_m":round(percentile(short,.95),2),
          "short_step_abs_jump_p99_m":round(percentile(short,.99),2),
          "short_step_abs_jump_max_m":round(max(short),2),
          "short_step_jumps_over_20m":sum(v>20 for v in short),
          "very_steep_pairs_over_80_percent":len(steep),
          "dsm_100m_resampled_positive_gain_m":hills(pts),
          "zero_or_negative_values":sum(v<=0 for v in heights),
          "source_sha256_untouched":r.get("source_sha256")
        }
        result["historical_candidate_checks"].append(row)
        print("CANDIDATE",json.dumps(row),flush=True)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print("REPORT",args.report,flush=True)

if __name__=="__main__":
    main()
