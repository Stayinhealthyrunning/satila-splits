#!/usr/bin/env python3
"""Desktop and mobile: excluded Grind may never appear in a live Sätila view.

Iterates ALL 27 editions with actual curated real-data fixture fetches and
proves each selected first 2025 segment starts from the race clock origin,
without using the owner's rejected nonofficial early checkpoint.
"""
from __future__ import annotations
import asyncio,json,os,re
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(os.getenv("SATILA_SITE","docs"))
EXPECTED_FIRST={
 "2025-trail22":("Start","Skolan",4),
 "2025-trail43":("Start","Torrås",6),
 "2025-ultra85":("Start","Navåsen",6),
}

async def main():
    boot=json.loads((ROOT/"data/bootstrap.json").read_text(encoding="utf-8"))
    assert len(boot["editions"])==27
    fixtures={"data/bootstrap.json":boot}
    for p in (ROOT/"data").glob("*.json"):
        fixtures["data/"+p.name]=json.loads(p.read_text(encoding="utf-8"))
    for p in (ROOT/"data/races").glob("*.json"):
        fixtures["data/races/"+p.name]=json.loads(p.read_text(encoding="utf-8"))
    for p in (ROOT/"data/routes").glob("*.json"):
        fixtures["data/routes/"+p.name]=json.loads(p.read_text(encoding="utf-8"))
    for ed in boot["editions"]:
        race=fixtures["data/races/"+ed["race_key"]+".json"]
        assert all(not re.fullmatch(r"grind",str(st["name"]).strip(),re.IGNORECASE) for st in race["stations"]),ed["race_key"]
        assert len(race["stations"])==ed["timing_stations"]
        assert all(sp["station_uid"] in {st["uid"] for st in race["stations"]} for sp in race["splits"])
        assert len(race["splits"])==ed["split_observations"]
    markup=(ROOT/"index.html").read_text(encoding="utf-8")
    markup=re.sub(r"<link [^>]*>","",markup)
    markup=re.sub(r"<script[^>]*>\s*</script>","",markup)
    script=(ROOT/"assets"/"app.js").read_text(encoding="utf-8")
    async with async_playwright() as p:
        opts={"headless":True}
        if Path("/usr/bin/chromium").exists():
            opts.update(executable_path="/usr/bin/chromium",args=["--no-sandbox"])
        browser=await p.chromium.launch(**opts)
        try:
            for width,height in ((1440,900),(390,844)):
                page=await browser.new_page(viewport={"width":width,"height":height})
                errors=[]
                page.on("pageerror",lambda error:errors.append(str(error)))
                await page.set_content(markup)
                await page.add_style_tag(content=(ROOT/"assets/style.css").read_text(encoding="utf-8"))
                await page.add_style_tag(content=(ROOT/"assets/style-extra.css").read_text(encoding="utf-8"))
                await page.evaluate("""data=>{
                  window.__fixtures=data;window.__missing=[];
                  window.fetch=async url=>{
                    const result=window.__fixtures[String(url)];
                    if(result===undefined)window.__missing.push(String(url));
                    return {ok:result!==undefined,status:result===undefined?404:200,json:async()=>result};
                  };
                }""",fixtures)
                await page.add_script_tag(content=script)
                await page.wait_for_function("document.querySelector('#source-indicator').textContent.includes('Verifierat EQ Timing')")
                visited=[]
                for family in ("trail22","trail43","ultra85"):
                    await page.locator(f'[data-family="{family}"]').click()
                    for ed in sorted((e for e in boot["editions"] if e["family"]==family),key=lambda e:e["year"],reverse=True):
                        await page.locator("#year-select").select_option(str(ed["year"]))
                        await page.wait_for_function("""ed=>{
                          const title=document.querySelector('#race-title')?.textContent||'';
                          const source=document.querySelector('#source-indicator')?.textContent||'';
                          return title.includes(String(ed.year)) && title.includes(ed.family==='trail22'?'22 km':ed.family==='trail43'?'43 km':'85 km')
                             && source.includes(String(ed.timing_stations)+' stationer');
                        }""",arg=ed)
                        await page.wait_for_function("document.querySelectorAll('#segment-table tbody tr').length>0")
                        for selector in ("#segments","#dynamics","#course","#course-intelligence","#history"):
                            content=await page.locator(selector).inner_text()
                            assert not re.search(r"\bGrind\b",content,re.IGNORECASE),(width,ed["race_key"],selector,content[:500])
                        if ed["race_key"] in EXPECTED_FIRST:
                            first,second,segments=EXPECTED_FIRST[ed["race_key"]]
                            labels=await page.locator("#segment-table tbody tr").all_inner_texts()
                            assert len(labels)==segments,(width,ed["race_key"],labels)
                            assert first in labels[0] and second in labels[0],(width,ed["race_key"],labels[0])
                            assert not any(re.search(r"\bGrind\b",x,re.IGNORECASE) for x in labels),ed["race_key"]
                        visited.append(ed["race_key"])
                assert len(visited)==len(set(visited))==27,(width,len(visited))
                assert not errors,(width,errors)
                assert not await page.evaluate("window.__missing"),(width,await page.evaluate("window.__missing"))
                print("PASS no nonofficial Grind in 27 editions and six/four accepted 2025 segments",width,flush=True)
                await page.close()
        finally:await browser.close()
if __name__=="__main__":asyncio.run(main())
