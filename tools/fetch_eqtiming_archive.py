#!/usr/bin/env python3
"""Capture public EQ Timing result traffic for every configured Sätila Trail edition.

The EQ Live application is JavaScript-driven. Instead of depending on undocumented
endpoint names, this adapter loads the public result view and records the XHR/fetch
responses used by EQ's own client. Raw responses are preserved with URL, status,
content type and SHA-256 so parsers can be improved without re-fetching.
"""
from __future__ import annotations
import argparse, asyncio, gzip, hashlib, json, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from playwright.async_api import async_playwright

ROOT=Path(__file__).resolve().parents[1]
CAT=ROOT/"config/eqtiming-events.json"

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def relevant(url,ctype):
    host=urlparse(url).netloc.lower()
    return ("eqtiming" in host and ("json" in (ctype or "").lower() or "/api/" in url.lower() or "result" in url.lower()))

async def capture_event(browser,event,outdir,wait_ms):
    year=event["year"]; eid=event["event_id"]; target=f'https://live.eqtiming.com/{eid}#result'
    ctx=await browser.new_context(locale="sv-SE")
    page=await ctx.new_page(); captured=[]; seen=set()
    async def on_response(resp):
        try:
            ctype=resp.headers.get("content-type","")
            if not relevant(resp.url,ctype): return
            body=await resp.body(); digest=sha(body)
            key=(resp.url,digest)
            if key in seen:return
            seen.add(key)
            ext=".json" if "json" in ctype.lower() else ".bin"
            fn=f"{len(captured):04d}-{digest[:16]}{ext}"
            (outdir/fn).write_bytes(body)
            captured.append({"url":resp.url,"status":resp.status,"content_type":ctype,"sha256":digest,"bytes":len(body),"file":fn})
        except Exception as exc:
            captured.append({"url":getattr(resp,"url",""),"capture_error":repr(exc)})
    page.on("response",on_response)
    nav_error=None
    try:
        await page.goto(target,wait_until="domcontentloaded",timeout=60000)
        await page.wait_for_timeout(wait_ms)
        # Exercise the public page so lazy-loaded result rows/pages are requested.
        for _ in range(12):
            await page.mouse.wheel(0,5000); await page.wait_for_timeout(350)
        # Click visible controls that plausibly expand/load result content, but never forms/login.
        for label in ["Resultat","Results","Visa fler","Show more","Nästa","Next"]:
            try:
                loc=page.get_by_text(label,exact=False)
                for i in range(min(await loc.count(),8)):
                    el=loc.nth(i)
                    if await el.is_visible():
                        await el.click(timeout=1200); await page.wait_for_timeout(500)
            except Exception: pass
        await page.wait_for_timeout(1500)
    except Exception as exc: nav_error=repr(exc)
    title=await page.title()
    html=await page.content()
    (outdir/"page.html").write_text(html,encoding="utf-8")
    await ctx.close()
    manifest={"schema_version":1,"year":year,"event_id":eid,"source_url":target,"title":title,
      "captured_at_utc":datetime.now(timezone.utc).isoformat(),"navigation_error":nav_error,
      "responses":captured,"response_count":len(captured)}
    (outdir/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return manifest

def build_sqlite(root,events):
    db=root/"satila-eqtiming-raw.sqlite"
    if db.exists():db.unlink()
    con=sqlite3.connect(db)
    con.executescript("""CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE events(year INTEGER PRIMARY KEY,event_id INTEGER NOT NULL,source_url TEXT NOT NULL,title TEXT,response_count INTEGER NOT NULL,navigation_error TEXT);
CREATE TABLE responses(year INTEGER NOT NULL,sequence_no INTEGER NOT NULL,url TEXT,status INTEGER,content_type TEXT,sha256 TEXT,bytes INTEGER,file TEXT,capture_error TEXT,PRIMARY KEY(year,sequence_no));
""")
    con.execute("INSERT INTO meta VALUES(?,?)",("provider","EQ Timing"))
    con.execute("INSERT INTO meta VALUES(?,?)",("event_key","satila-trail"))
    con.execute("INSERT INTO meta VALUES(?,?)",("created_at_utc",datetime.now(timezone.utc).isoformat()))
    for m in events:
        con.execute("INSERT INTO events VALUES(?,?,?,?,?,?)",(m["year"],m["event_id"],m["source_url"],m.get("title"),m["response_count"],m.get("navigation_error")))
        for i,r in enumerate(m["responses"]):
            con.execute("INSERT INTO responses VALUES(?,?,?,?,?,?,?,?,?)",(m["year"],i,r.get("url"),r.get("status"),r.get("content_type"),r.get("sha256"),r.get("bytes"),r.get("file"),r.get("capture_error")))
    con.commit()
    integrity=con.execute("PRAGMA integrity_check").fetchone()[0];con.close()
    if integrity!="ok":raise SystemExit("SQLite integrity check failed: "+integrity)
    gz=Path(str(db)+".gz")
    with db.open("rb") as src,gzip.GzipFile(filename="",mode="wb",fileobj=gz.open("wb"),compresslevel=9,mtime=0) as z:
        z.write(src.read())
    return db,gz

async def main_async(args):
    cat=json.loads(CAT.read_text(encoding="utf-8"))
    chosen=[e for e in cat["events"] if not args.year or e["year"]==args.year]
    out=ROOT/args.output;out.mkdir(parents=True,exist_ok=True)
    manifests=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        for e in chosen:
            d=out/str(e["year"]);d.mkdir(parents=True,exist_ok=True)
            print(f'Capturing EQ Timing {e["year"]} event {e["event_id"]}',flush=True)
            manifests.append(await capture_event(browser,e,d,args.wait_ms))
        await browser.close()
    db,gz=build_sqlite(out,manifests)
    summary={"events":[{"year":m["year"],"event_id":m["event_id"],"responses":m["response_count"],"navigation_error":m["navigation_error"]} for m in manifests],
      "database":str(db.relative_to(ROOT)),"compressed":str(gz.relative_to(ROOT))}
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    if not manifests or all(m["response_count"]==0 for m in manifests):
        raise SystemExit("No EQ Timing result/API responses captured; refusing false-success archive")

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--year",type=int);ap.add_argument("--output",default="data/work/eqtiming");ap.add_argument("--wait-ms",type=int,default=9000)
    args=ap.parse_args();asyncio.run(main_async(args))
if __name__=="__main__":main()
