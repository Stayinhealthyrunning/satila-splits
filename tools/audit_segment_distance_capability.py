#!/usr/bin/env python3
"""Audit whether timing-axis km metadata is safe for pace-derived analytics.

TIME observations can be valid even when a station's public km metadata is not
sufficiently trustworthy as physical travelled distance. This script never
changes source km. It emits a capability report and hard-flags only obviously
implausible *median field speed* over segments >=3 km (>20 km/h), which is a
sanity signal for metadata/axis mismatch rather than an athlete judgement.
"""
from __future__ import annotations
import argparse,collections,json,math,statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"docs"/"data"

def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",default=str(ROOT))
    ap.add_argument("--output")
    args=ap.parse_args()
    root=Path(args.data)
    editions=load(root/"bootstrap.json")["editions"]
    rows=[];suspect=[]
    for ed in editions:
        race=load(root/"races"/f"{ed['race_key']}.json")
        counts=collections.Counter(s["station_uid"] for s in race["splits"])
        bounds=[{"uid":"start","name":"Start","km":0}]+[
            s for s in sorted(race["stations"],key=lambda x:(x["sort"],x.get("km") or 0))
            if s["is_analysis_boundary"] and isinstance(s.get("km"),(int,float))
            and s["km"]>0 and counts[s["uid"]]>0
        ]
        lookup=collections.defaultdict(dict)
        for s in race["splits"]: lookup[s["result_id"]][s["station_uid"]]=s["elapsed_seconds"]
        finish=[r for r in race["results"] if r["status"]=="FINISHED" and r.get("finish_seconds")]
        segments=[]
        for i,(a,b) in enumerate(zip(bounds,bounds[1:]),start=1):
            km=b["km"]-a["km"]
            if km<=0: continue
            values=[]
            for r in finish:
                own=lookup[r["id"]]
                ta=0 if a["uid"]=="start" else own.get(a["uid"])
                tb=own.get(b["uid"])
                if isinstance(ta,(int,float)) and isinstance(tb,(int,float)) and tb>ta:
                    values.append(tb-ta)
            median_sec=statistics.median(values) if len(values)>=5 else None
            speed=(km/(median_sec/3600)) if median_sec else None
            implausible=bool(speed is not None and km>=3 and speed>20)
            item={
              "from":a["name"],"to":b["name"],"timing_km":round(km,3),
              "n":len(values),
              "median_segment_seconds":round(median_sec,3) if median_sec is not None else None,
              "median_implied_kmh":round(speed,3) if speed is not None else None,
              "pace_distance_sanity":"FAIL_IMPLAUSIBLE_HIGH_MEDIAN_SPEED" if implausible else
                                     "PASS_BASIC_SANITY" if speed is not None else "INSUFFICIENT_N",
              "pace_analytics_note":"Timing km metadata requires independent segment-distance evidence; basic sanity pass is not route verification."
            }
            segments.append(item)
            if implausible:
                suspect.append({"race_key":race["race_key"],**item})
        rows.append({"race_key":race["race_key"],"segments":segments,
                     "suspect_segment_count":sum(x["pace_distance_sanity"].startswith("FAIL") for x in segments)})
    out={
      "schema":"satila-segment-distance-capability-v1",
      "method":"Exact public TIME pairs; effective observed boundaries; median implied speed is only a sanity screen, not proof of route distance.",
      "hard_sanity_rule":"segment timing_km >= 3 and field-median implied speed > 20 km/h => do not use this km metadata for pace/retention without independent distance verification",
      "editions":rows,"suspect_segments":suspect
    }
    if args.output:
        p=Path(args.output);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PACE-DISTANCE SANITY SUSPECT SEGMENTS:",len(suspect))
    for x in suspect:
        print(f"{x['race_key']} | {x['from']} -> {x['to']} | {x['timing_km']} km | n={x['n']} | implied median {x['median_implied_kmh']} km/h")
    # The historical 2023 Torrås km metadata was explicitly migrated from 8.0 to 16.2.
    # Its formerly implausible 16 km Torrås -> Almered interval must no longer recur.
    race2023=next(r for r in rows if r["race_key"]=="2023-trail43")
    torras=next(s for s in race2023["segments"] if s["from"]=="Torrås" and s["to"]=="Almered")
    assert math.isclose(torras["timing_km"],7.8), "2023 Torrås -> Almered must use corrected 16.2 km Torrås boundary"
    assert torras["pace_distance_sanity"]=="PASS_BASIC_SANITY", "Corrected Torrås interval failed basic sanity"
    assert len(rows)==27
    print("SEGMENT DISTANCE CAPABILITY AUDIT PASSED")

if __name__=="__main__":
    main()
