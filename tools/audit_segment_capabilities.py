#!/usr/bin/env python3
"""Race-specific segment capability matrix, derived solely from public TIME pairs.

Conservative parity with the first-draft Engine adapter: finishers, exact and
monotonically increasing observations, analysis-boundary stations, start=0 only.
Produces an auditable table/JSON for Codex and frontend feature gating.
No athlete identifiers/names are included in the published report.
"""
from __future__ import annotations
import argparse
import collections
import json
from pathlib import Path

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data",default=str(Path(__file__).resolve().parents[1]/"docs"/"data"))
    p.add_argument("--output",default=None,help="Optional JSON output (CI artifact)")
    args=p.parse_args()
    root=Path(args.data)
    catalog=load(root/"bootstrap.json")["editions"]
    report=[]
    for ed in sorted(catalog,key=lambda e:(e["year"],e["family"])):
        race=load(root/"races"/(ed["race_key"]+".json"))
        boundaries=[{"uid":"start","name":"Start","km":0}]+[
          x for x in sorted(race["stations"],key=lambda s:(s["sort"],s.get("km") or 0))
          if x["is_analysis_boundary"] and isinstance(x.get("km"),(int,float)) and x["km"]>0]
        lookup=collections.defaultdict(dict)
        for s in race["splits"]:
            lookup[s["result_id"]][s["station_uid"]]=s
        finishers=[r for r in race["results"] if r["status"]=="FINISHED" and r.get("finish_seconds")]
        available=[]
        for i in range(1,len(boundaries)):
            first,last=boundaries[i-1],boundaries[i]
            km=last["km"]-first["km"]
            if km<=0:
                continue
            groups=collections.Counter()
            pair_count=0
            fractions=[]
            for r in finishers:
                a={"elapsed_seconds":0} if i==1 else lookup[r["id"]].get(first["uid"])
                b=lookup[r["id"]].get(last["uid"])
                if not a or not b:
                    continue
                ta,tb=a["elapsed_seconds"],b["elapsed_seconds"]
                if not isinstance(ta,(int,float)) or not isinstance(tb,(int,float)) or tb<=ta:
                    continue
                pair_count+=1
                groups[r["sex"] if r.get("sex") in ("F","M") else "unknown"]+=1
                fractions.append((tb-ta)/r["finish_seconds"])
            gap={"index":i-1,"from":first["name"],"to":last["name"],"source_timing_km":round(km,3),
                 "valid_finishers":pair_count,"field_median":pair_count>=5,
                 "q25_q75":pair_count>=10,"q10_q90":pair_count>=20,
                 "women":groups["F"],"men":groups["M"],
                 "women_median":groups["F"]>=5,"men_median":groups["M"]>=5,
                 "sex_podium_possible":groups["F"]>=3 and groups["M"]>=3,
                 "pooled_goal_plan":len(fractions)>=5}
            available.append(gap)
        full_medians=sum(s["field_median"] for s in available)
        pooled=sum(s["pooled_goal_plan"] for s in available)
        report.append({"race_key":ed["race_key"],"year":ed["year"],"family":ed["family"],
                       "finishers":len(finishers),"observed_source_splits":len(race["splits"]),
                       "timing_stations":len(race["stations"]),
                       "analysable_segments":len(available),"median_ready_segments":full_medians,
                       "q25_q75_ready_segments":sum(x["q25_q75"] for x in available),
                       "q10_q90_ready_segments":sum(x["q10_q90"] for x in available),
                       "dual_sex_median_segments":sum(x["women_median"] and x["men_median"] for x in available),
                       "pooled_goal_plan_complete":bool(available) and len(available)==pooled,
                       "segment_capabilities":available})
    result={"schema":"satila-exact-pair-capability-v1","scope":"27 editions; FINISHED only; exact positive TIME segment pairs",
            "thresholds":{"median":5,"q25_q75":10,"q10_q90":20,
                          "sex_specific_median_each":5,"sex_podium_each":3,"goal_fraction":5},
            "editions":report}
    if args.output:
        path=Path(args.output)
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("race_key | finishers | observed TIME | analysis segments | median-ready | Q25/Q75 | Q10/Q90 | both-sex median | all pooled plan")
    for r in report:
        print(f"{r['race_key']} | {r['finishers']} | {r['observed_source_splits']} | {r['analysable_segments']} | {r['median_ready_segments']} | {r['q25_q75_ready_segments']} | {r['q10_q90_ready_segments']} | {r['dual_sex_median_segments']} | {r['pooled_goal_plan_complete']}")
    assert len(report)==27
    assert sum(r["finishers"] for r in report)==2649
    assert all(s["valid_finishers"]<=r["finishers"] for r in report for s in r["segment_capabilities"])
    assert all(s["q10_q90"]<=s["q25_q75"]<=s["field_median"] for r in report for s in r["segment_capabilities"])
    assert all(s["women"]+s["men"]<=s["valid_finishers"] for r in report for s in r["segment_capabilities"])
    print("CAPABILITY CHECKS PASSED")

if __name__=="__main__":
    main()
