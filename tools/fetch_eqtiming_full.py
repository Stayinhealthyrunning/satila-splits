#!/usr/bin/env python3
"""Fetch every public EQ Timing result station for configured Sätila editions.

Source observations are preserved verbatim. Only stations explicitly marked
public by EQ are queried. Pagination continues until EQ reports all items.
"""
from __future__ import annotations
import asyncio, json, hashlib
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path(__file__).resolve().parents[1]
CAT=ROOT/"config/eqtiming-events.json"
OUT=ROOT/"data/work/eqtiming-full"

def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=json.dumps(obj,ensure_ascii=False,indent=2).encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()

async def get_json(req,url):
    r=await req.get(url,timeout=60000)
    if not r.ok: raise RuntimeError(f"{r.status} {url}")
    return await r.json()

async def main():
    cat=json.loads(CAT.read_text())
    OUT.mkdir(parents=True,exist_ok=True)
    summary=[]
    async with async_playwright() as p:
      req=await p.request.new_context(extra_http_headers={"Accept":"application/json"})
      for e in cat["events"]:
        y=e["year"]; eid=e["event_id"]; yd=OUT/str(y); yd.mkdir(parents=True,exist_ok=True)
        print(f"FULL {y} event {eid}",flush=True)
        event=await get_json(req,f"https://live.eqtiming.com/api/Event/{eid}")
        dump(yd/"event.json",event)
        try:
            contestants=await get_json(req,f"https://live.eqtiming.com/api/Contestants/{eid}")
            dump(yd/"contestants.json",contestants)
        except Exception as ex:
            contestants=None
            (yd/"contestants-error.txt").write_text(repr(ex))
        stations=[s for s in (event.get("StasjonsOppsett") or {}).values() if s.get("Er_offentlig") is True and s.get("EtappeUID")]
        races=event.get("Etapper") or {}
        station_rows=[]; total_items=0
        for s in sorted(stations,key=lambda z:(z.get("EtappeUID",0),z.get("Sortering",0),z.get("Km",0))):
            leg=int(s["EtappeUID"]); station=int(s["UID"]); start=1; pages=0; station_items=0
            while True:
                url=f"https://live.eqtiming.com/api/Result/Total/{eid}/{leg}?justTimeData=true&count=100&startAt={start}&station={station}&query=&round=1&passes=false"
                data=await get_json(req,url)
                pages+=1; n=len(data.get("Items") or []); station_items+=n; total_items+=n
                dump(yd/"results"/str(leg)/str(station)/f"{start:06d}.json",data)
                total=int(data.get("TotalItems") or data.get("ItemCount") or n)
                if n==0 or start+n>total or n<100: break
                start+=n
                if pages>100: raise RuntimeError(f"pagination guard {y}/{leg}/{station}")
            station_rows.append({"race_uid":leg,"race_name":(races.get(str(leg)) or races.get(leg) or {}).get("Navn"),
              "station_uid":station,"station_name":s.get("Navn"),"km":s.get("Km"),"sort":s.get("Sortering"),
              "is_finish":s.get("Er_stopp"),"pages":pages,"items":station_items})
            print(f"  {leg} {station} {s.get('Navn')} km={s.get('Km')} items={station_items}",flush=True)
        manifest={"year":y,"event_id":eid,"event_name":event.get("Navn"),"races":[{"uid":int(k),"name":v.get("Navn")} for k,v in races.items()],
          "public_stations":station_rows,"station_count":len(station_rows),"result_observations":total_items,
          "contestants_captured":contestants is not None}
        dump(yd/"manifest.json",manifest); summary.append(manifest)
      await req.dispose()
    dump(OUT/"summary.json",summary)
    if not summary or any(x["station_count"]==0 for x in summary):
        raise SystemExit("At least one configured edition has no public EQ stations; inspect before accepting archive")

asyncio.run(main())
