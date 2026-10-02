#!/usr/bin/env python3
"""Source-driven UI readiness for real runner and podium components (27 editions).

This is an evidence inventory, not a synthetic race rating. The output contains
aggregates only and publishes no individual identities.
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"docs"/"data"

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def valid_place(v):
    return type(v) is int and v>0

def audit(data=ROOT):
    boot=read(data/"bootstrap.json")
    matrix=[]
    for ed in boot["editions"]:
        race=read(data/"races"/f"{ed['race_key']}.json")
        source_count=collections.Counter(s["station_uid"] for s in race["splits"])
        stations=sorted((s for s in race["stations"] if s["is_analysis_boundary"] and
                        isinstance(s.get("km"),(int,float)) and s["km"]>0 and source_count[s["uid"]]),
                        key=lambda s:(s["sort"],s["km"],s["uid"]))
        boundary=[{"uid":"start","name":"Start","km":0}]+stations
        split_lookup=collections.defaultdict(dict)
        for s in race["splits"]:
            split_lookup[s["result_id"]][s["station_uid"]]=s
        finishers=[r for r in race["results"] if r["status"]=="FINISHED" and
                   isinstance(r.get("finish_seconds"),(float,int)) and r["finish_seconds"]>0]
        sexes=collections.Counter(r.get("sex") if r.get("sex") in ("F","M") else "unknown" for r in finishers)
        pair_count=collections.defaultdict(int)
        pair_sexes=collections.defaultdict(collections.Counter)
        valid_rank_journey=0
        two_plus_segments=0
        for r in finishers:
            sid=r["id"]
            obs=split_lookup[sid]
            ranked=sum(valid_place(obs[s["uid"]].get("place")) for s in stations if s["uid"] in obs)
            if ranked>=2:
                valid_rank_journey+=1
            runner_pairs=0
            for idx in range(1,len(boundary)):
                first,last=boundary[idx-1],boundary[idx]
                if last["km"]<=first["km"]:
                    continue
                ta=0 if first["uid"]=="start" else obs.get(first["uid"],{}).get("elapsed_seconds")
                tb=obs.get(last["uid"],{}).get("elapsed_seconds")
                if ta is None or tb is None or tb<=ta:
                    continue
                pair_count[idx-1]+=1
                pair_sexes[idx-1][r.get("sex") if r.get("sex") in ("F","M") else "unknown"]+=1
                runner_pairs+=1
            if runner_pairs>=2:
                two_plus_segments+=1

        analyses=[]
        for idx in range(1,len(boundary)):
            x,y=boundary[idx-1:idx+1]
            if y["km"]<=x["km"]: continue
            n=pair_count[idx-1]
            sexes_i=pair_sexes[idx-1]
            analyses.append({"from":x["name"],"to":y["name"],
                             "n":n,"women":sexes_i["F"],"men":sexes_i["M"],
                             "pooled_median":n>=5,"pooled_quartiles":n>=10,
                             "pooled_deciles":n>=20,
                             "both_sexes_top3":sexes_i["F"]>=3 and sexes_i["M"]>=3,
                             "both_sexes_median":sexes_i["F"]>=5 and sexes_i["M"]>=5})

        matrix.append({
            "race_key":ed["race_key"],
            "finishers":len(finishers),
            "female_finishers":sexes["F"],
            "male_finishers":sexes["M"],
            "sex_unknown_finishers":sexes["unknown"],
            "finish_podium_both_sexes":sexes["F"]>=3 and sexes["M"]>=3,
            "ranked_finishers_with_2plus_real_place_observations":valid_rank_journey,
            "finishers_with_2plus_valid_adjacent_segments":two_plus_segments,
            "personal_segment_insights_available":two_plus_segments>0,
            "two_person_time_comparison_available":len(finishers)>=2,
            "verified_local_route_available":bool(ed.get("route_file")),
            "effective_segment_count":len(analyses),
            "segment_podium_both_sexes_count":sum(x["both_sexes_top3"] for x in analyses),
            "segment_median_both_sexes_count":sum(x["both_sexes_median"] for x in analyses),
            "segment_decile_count":sum(x["pooled_deciles"] for x in analyses),
            "per_segment":analyses,
        })
    assert len(matrix)==27
    assert sum(r["finishers"] for r in matrix)==2649
    assert all(r["segment_median_both_sexes_count"]<=r["effective_segment_count"] for r in matrix)
    assert all(r["segment_podium_both_sexes_count"]<=r["effective_segment_count"] for r in matrix)
    assert all(r["ranked_finishers_with_2plus_real_place_observations"]<=r["finishers"] for r in matrix)
    assert all(r["finishers_with_2plus_valid_adjacent_segments"]<=r["finishers"] for r in matrix)
    return {"schema":"satila-ui-capability-v1",
            "method":"Exact public TIME/Total-place observations among FINISHED; effective boundaries exclude only globally zero-observation metadata stations.",
            "editions":matrix}

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",default=str(ROOT))
    ap.add_argument("--output",default=None)
    args=ap.parse_args()
    out=audit(Path(args.data))
    if args.output:
        f=Path(args.output)
        f.parent.mkdir(parents=True,exist_ok=True)
        f.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("race_key | F | M | rank-journies | profiles>=2 segments | both-sex finish podium | both-sex segment podia | both-sex segment medians | route")
    for r in sorted(out["editions"],key=lambda x:x["race_key"]):
        print(f"{r['race_key']} | {r['female_finishers']} | {r['male_finishers']} | {r['ranked_finishers_with_2plus_real_place_observations']} | {r['finishers_with_2plus_valid_adjacent_segments']} | {r['finish_podium_both_sexes']} | {r['segment_podium_both_sexes_count']}/{r['effective_segment_count']} | {r['segment_median_both_sexes_count']}/{r['effective_segment_count']} | {r['verified_local_route_available']}")
    print("UI READINESS SOURCE TESTS PASSED")
