#!/usr/bin/env python3
"""Detect stations declared public but containing zero TIME observations.

The source station is always preserved. For an optional observed-only analysis
axis, omit zero-observation intermediate boundaries and use the exact difference
between the neighboring *recorded* TIME anchors. Never create a timestamp at an
absent station or redistribute that observed span under false timing precision.
"""
from __future__ import annotations
import collections
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"docs"/"data"

def matrix(root=ROOT):
    bootstrap=json.loads((root/"bootstrap.json").read_text(encoding="utf-8"))
    result=[]
    for ed in bootstrap["editions"]:
        race=json.loads((root/"races"/f"{ed['race_key']}.json").read_text(encoding="utf-8"))
        counts=collections.Counter(s["station_uid"] for s in race["splits"])
        original=[x for x in sorted(race["stations"],key=lambda s:(s["sort"],s.get("km") or 0))
                  if x["is_analysis_boundary"] and isinstance(x.get("km"),(int,float)) and x["km"]>0]
        metadata_only=[{"uid":st["uid"],"name":st["name"],"km":st.get("km"),"is_analysis_boundary":st["is_analysis_boundary"]}
                       for st in race["stations"] if not counts[st["uid"]]]
        zero=[{"uid":st["uid"],"name":st["name"],"km":st["km"]} for st in original if not counts[st["uid"]]]
        active=[{"uid":"start","name":"Start","km":0}]+[s for s in original if counts[s["uid"]]]
        observed=collections.defaultdict(dict)
        for s in race["splits"]:
            observed[s["result_id"]][s["station_uid"]]=s["elapsed_seconds"]
        finishers=[r for r in race["results"] if r["status"]=="FINISHED" and r.get("finish_seconds")]
        bridges=[]
        for i in range(1,len(active)):
            a,b=active[i-1:i+1]
            if b["km"]<=a["km"]:
                continue
            original_between=[o["name"] for o in race["stations"] if o["name"] in {z["name"] for z in metadata_only}
                              and isinstance(o.get("km"),(float,int)) and a["km"]<o["km"]<b["km"]]
            n=0
            for r in finishers:
                o=observed[r["id"]]
                ta=0 if a["uid"]=="start" else o.get(a["uid"])
                tb=o.get(b["uid"])
                if ta is not None and tb is not None and tb>ta:
                    n+=1
            bridges.append({"from":a["name"],"to":b["name"],"timing_km":round(b["km"]-a["km"],3),
                            "valid_exact_time_pairs":n,
                            "bypassed_zero_time_stations":original_between,
                            "median_eligible":n>=5,"q25_q75_eligible":n>=10,"q10_q90_eligible":n>=20})
        result.append({"race_key":ed["race_key"],"metadata_only_stations":metadata_only,
                       "zero_observation_analysis_stations":zero,
                       "source_declared_boundaries":len(original),
                       "observed_only_boundaries":len(active)-1,
                       "observed_only_segments":bridges})
    return result

if __name__=="__main__":
    rows=matrix()
    anomalies=[r for r in rows if r["zero_observation_analysis_stations"]]
    print("Edition | zero-observation source boundaries | valid observed-only bridge segments")
    for r in anomalies:
        for z in r["zero_observation_analysis_stations"]:
            print(f"{r['race_key']} | {z['name']} (km {z['km']}, UID {z['uid']}) | zero public TIME observations")
        for s in r["observed_only_segments"]:
            if s["bypassed_zero_time_stations"]:
                print(f"  ACTUAL PAIR: {s['from']} -> {s['to']}; n={s['valid_exact_time_pairs']}; bypasses {','.join(s['bypassed_zero_time_stations'])}; median={s['median_eligible']}")
    print(f"ZERO-TIME ANALYSIS-BOUNDARY EDITIONS: {len(anomalies)} of {len(rows)}")
    target=next(r for r in rows if r["race_key"]=="2025-trail43")
    assert any(x["name"]=="Tostared" and x["km"]==10.2 and x["uid"]==1416266
               for x in target["metadata_only_stations"])
    bridge=next(x for x in target["observed_only_segments"] if x["from"]=="Grind" and x["to"]=="Torrås")
    assert bridge["valid_exact_time_pairs"]>=100, bridge
    assert bridge["bypassed_zero_time_stations"]==["Tostared"], bridge
    assert all(s["valid_exact_time_pairs"]>=0 for r in rows for s in r["observed_only_segments"])
    assert len(rows)==27
    print("STATION COVERAGE AND SOURCE-ANCHORED BRIDGE CHECKS PASSED")
