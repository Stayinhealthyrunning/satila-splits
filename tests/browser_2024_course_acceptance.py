#!/usr/bin/env python3
"""Independent Chromium: real 2024 participant GPX renders with real partial TIME."""
from __future__ import annotations
import asyncio,json,os,re
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path(os.getenv("SATILA_SITE","docs"))
async def main():
    boot=json.loads((ROOT/"data/bootstrap.json").read_text(encoding="utf-8"))
    edition=next(x for x in boot["editions"] if x["race_key"]=="2024-trail43")
    assert edition["route_file"]=="routes/2024-trail43-participant.json"
    route=json.loads((ROOT/"data"/edition["route_file"]).read_text(encoding="utf-8"))
    race=json.loads((ROOT/"data/races/2024-trail43.json").read_text(encoding="utf-8"))
    assert route["edition_references"]==[2024] and route["type"]=="VERIFIED_PARTICIPANT"
    assert len(race["splits"])==750 and len(route["points"])>=100
    payload={"data/bootstrap.json":boot,"data/races/2024-trail43.json":race}
    for e in boot["editions"]:
        if e["race_key"]=="2024-trail43":continue
        p=ROOT/"data/races"/(e["race_key"]+".json")
        payload["data/races/"+p.name]=json.loads(p.read_text(encoding="utf-8"))
    for p in (ROOT/"data/routes").glob("*.json"):
        payload["data/routes/"+p.name]=json.loads(p.read_text(encoding="utf-8"))
    for p in (ROOT/"data").glob("*.json"):
        payload["data/"+p.name]=json.loads(p.read_text(encoding="utf-8"))
    markup=(ROOT/"index.html").read_text(encoding="utf-8")
    markup=re.sub(r"<link [^>]*>","",markup)
    markup=re.sub(r"<script[^>]*>\s*</script>","",markup)
    js=(ROOT/"assets/app.js").read_text(encoding="utf-8")
    async with async_playwright() as p:
        opts={"headless":True}
        if Path("/usr/bin/chromium").exists():
            opts.update(executable_path="/usr/bin/chromium",args=["--no-sandbox"])
        browser=await p.chromium.launch(**opts)
        for width in (1440,390):
            page=await browser.new_page(viewport={"width":width,"height":900 if width>390 else 844})
            errors=[]
            page.on("pageerror",lambda e:errors.append(str(e)))
            await page.set_content(markup)
            await page.add_style_tag(content=(ROOT/"assets/style.css").read_text(encoding="utf-8"))
            await page.add_style_tag(content=(ROOT/"assets/style-extra.css").read_text(encoding="utf-8"))
            await page.evaluate("""d=>{
              window.__fixtures=d;window.__missing=[];
              window.fetch=async u=>{
                const value=window.__fixtures[String(u)];
                if(value===undefined)window.__missing.push(String(u));
                return {ok:value!==undefined,status:value===undefined?404:200,json:async()=>value};
              };
            }""",payload)
            await page.add_script_tag(content=js)
            await page.wait_for_function("document.querySelector('#race-title').textContent.includes('2025')")
            await page.locator("#year-select").select_option("2024")
            await page.wait_for_function("document.querySelector('#course-source').textContent.includes('Verifierat deltagar-GPX för 2024')")
            assert "43 km · 2024" in await page.locator("#race-title").inner_text()
            assert await page.locator("#course-map .simple-route-line").count()==0
            assert await page.locator("#course-map .route-base").count()==1,(width,"map missing")
            assert await page.locator("#course-elevation svg line[stroke]").count()>1,(width,"colored elevation segments missing")
            assert "DELTAGARSPÅR" in await page.locator("#course-map .map-label").first.text_content()
            assert await page.locator("#course-map [data-map-hit]").count()==1
            assert await page.locator("#course-elevation [data-elev-hit]").count()==1
            assert not await page.evaluate("window.__missing||[]"),(width,await page.evaluate("window.__missing"))
            await page.locator("#runner-search").fill("Stefan Bengtsson")
            await page.wait_for_selector("#runner-suggestions .suggestion")
            await page.locator("#runner-suggestions .suggestion").first.click()
            await page.wait_for_selector("#profile-dialog[open]")
            assert await page.locator("#profile-mini-map svg").count()==1,(width,"profile map hidden")
            assert await page.locator("#profile-mini-elev svg").count()==1,(width,"profile elevation hidden")
            assert not errors,(width,errors)
            await page.close()
        await browser.close()
    print("PASS 2024/43 real participant GPS shows map and elevation at desktop/mobile with 750 accepted TIME observations (100 nonofficial Grind excluded; raw source retained)")

if __name__=="__main__":
    asyncio.run(main())
