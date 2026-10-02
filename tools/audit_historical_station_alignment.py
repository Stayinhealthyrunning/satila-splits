#!/usr/bin/env python3
"""Year-to-year public checkpoint evidence matrix for Sätila race history.

A shared checkpoint name/distance is not a verified same-course segment:
the 43-km participant GPX evidence records a major 2022 -> 2023 redesign
despite many unchanged checkpoint kilometer labels. Analysis stays gated by
promoted whole-course version, NOT solely by matching time station labels.
"""
from __future__ import annotations
import argparse
import collections
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"docs"/"data"
FAMILIES=("ultra85","trail43","trail22")

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def checkpoint_rows(race):
    cnt=collections.Counter(s["station_uid"] for s in race["splits"])
    return {s["name"].casefold().strip():{
        "source_name":s["name"],"km":s.get("km"),"uid":s["uid"],
        "is_analysis_boundary":s["is_analysis_boundary"],
        "public_time_count":cnt[s["uid"]]}
        for s in race["stations"] if s["is_analysis_boundary"] and isinstance(s.get("km"),(int,float))}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data",default=str(DATA))
    p.add_argument("--course-config",default=str(ROOT/"config/course-versions.json"))
    p.add_argument("--output")
    args=p.parse_args()
    root=Path(args.data)
    bootstrap=read(root/"bootstrap.json")
    candidates=read(Path(args.course_config))
    rows={ed["race_key"]:read(root/"races"/(ed["race_key"]+".json"))
          for ed in bootstrap["editions"]}
    out=[]
    for family in FAMILIES:
        years=sorted(ed["year"] for ed in bootstrap["editions"] if ed["family"]==family)
        for oldyear,newyear in zip(years,years[1:]):
            older=rows[f"{oldyear}-{family}"]
            newer=rows[f"{newyear}-{family}"]
            a,b=checkpoint_rows(older),checkpoint_rows(newer)
            shifts=[]
            for name in sorted(set(a)&set(b)):
                prev,curr=a[name],b[name]
                d=curr["km"]-prev["km"]
                shifts.append({"name":curr["source_name"],
                               "previous_timing_km":prev["km"],
                               "current_timing_km":curr["km"],
                               "timing_km_delta":round(d,3),
                               "previous_time_n":prev["public_time_count"],
                               "current_time_n":curr["public_time_count"],
                               "both_have_time":prev["public_time_count"]>0 and curr["public_time_count"]>0})
            labels={k:(len(a[k]["source_name"])>0) for k in set(a)&set(b)}
            old_ver=older.get("course_version")
            new_ver=newer.get("course_version")
            accepted=(old_ver==new_ver and old_ver is not None and
                older.get("route_status") in ("official_verified","organizer_2025_2026_reuse_assumption") and
                newer.get("route_status") in ("official_verified","organizer_2025_2026_reuse_assumption"))
            candidate_groups=None
            if family=="trail43":
                yr=candidates.get("year_candidates",{})
                candidate_groups=[yr.get(str(y),{}).get("comparison_group") for y in (oldyear,newyear)]
            out.append({
                "family":family,"from_year":oldyear,"to_year":newyear,
                "previous_nominal_km":older["nominal_km"],"current_nominal_km":newer["nominal_km"],
                "previous_course_version":old_ver,"current_course_version":new_ver,
                "matching_station_names":len(shifts),
                "same_label_does_not_certify_same_course":True,
                "large_timing_axis_shifts":[s for s in shifts if abs(s["timing_km_delta"])>=.5],
                "metadata_only_shared":[s for s in shifts if not s["both_have_time"]],
                "all_shared":shifts,
                "candidate_comparison_groups":candidate_groups,
                "whole_course_comparison_approved":bool(accepted)
            })
    assert len(out)==3*8
    critical=next(x for x in out if x["family"]=="trail43" and
                  x["from_year"]==2024 and x["to_year"]==2025)
    torras=next(x for x in critical["large_timing_axis_shifts"] if x["name"]=="Torrås")
    assert abs(torras["timing_km_delta"]-8.2)<1e-6,torras
    other=next(x for x in out if x["family"]=="trail43" and
               x["from_year"]==2022 and x["to_year"]==2023)
    assert other["candidate_comparison_groups"]==["trail43-2021-2022","trail43-2023-2025"]
    assert not other["whole_course_comparison_approved"]
    assert all(not x["whole_course_comparison_approved"] for x in out), "Do not automatically approve historic course comparisons"
    result={"schema":"satila-historical-checkpoint-alignment-v1",
            "warning":"Matching checkpoint labels or km do not prove an equivalent route or transferable historical pacing.",
            "pair_count":len(out),"pairs":out}
    if args.output:
        file=Path(args.output)
        file.parent.mkdir(parents=True,exist_ok=True)
        file.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("family | from -> to | shared names | changed km >=0.5 | any historic whole-course comparison approved")
    for x in out:
        print(f"{x['family']} | {x['from_year']} -> {x['to_year']} | {x['matching_station_names']} | {len(x['large_timing_axis_shifts'])} | {x['whole_course_comparison_approved']}")
    print(f"CRITICAL: 2024 -> 2025 43-km Torrås timing-label shift: +{torras['timing_km_delta']:.1f} km; 2022 -> 2023 candidate route groups differ despite shared timing labels.")
    print("HISTORICAL CHECKPOINT ALIGNMENT PASS: labels never stand in for verified course versions.")

if __name__=="__main__":
    main()
