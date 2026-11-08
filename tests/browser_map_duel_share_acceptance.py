#!/usr/bin/env python3
"""Real-browser share-link contract for 2–5 selected public Kartduell runners."""
from __future__ import annotations
import asyncio,json,os,re
from pathlib import Path
from urllib.parse import parse_qs,urlsplit,urlunsplit,urlencode
from playwright.async_api import async_playwright

ROOT=Path(os.getenv("SATILA_SITE","docs"))
HTML=re.sub(r"<script[^>]*>\s*</script>","",(ROOT/"index.html").read_text(encoding="utf-8"))
HTML=re.sub(r"<link [^>]*>","",HTML)
DATA={"data/bootstrap.json":json.loads((ROOT/"data/bootstrap.json").read_text(encoding="utf-8"))}
for folder in (ROOT/"data",ROOT/"data/races",ROOT/"data/routes"):
    for f in folder.glob("*.json"):
        DATA["data/"+f.relative_to(ROOT/"data").as_posix()]=json.loads(f.read_text(encoding="utf-8"))

async def new_page(browser,url="http://satila.test/"):
    page=await browser.new_page(viewport={"width":390,"height":844})
    async def serve(route):await route.fulfill(status=200,content_type="text/html",body=HTML)
    await page.route("http://satila.test/**",serve)
    await page.goto(url)
    for css in ("style.css","style-extra.css"):
        await page.add_style_tag(content=(ROOT/"assets"/css).read_text(encoding="utf-8"))
    await page.evaluate("""data=>{
      window.__fixtures=data;window.__copiedMapDuel=null;
      window.fetch=async u=>{
        const v=window.__fixtures[String(u)];
        return {ok:v!==undefined,status:v===undefined?404:200,json:async()=>v};
      };
      Object.defineProperty(navigator,'clipboard',{configurable:true,value:{
        writeText:async text=>{window.__copiedMapDuel=text}
      }});
    }""",DATA)
    for script in ("multi-year-map.js","multi-year-comparison.js","app.js"):
        await page.add_script_tag(content=(ROOT/"assets"/script).read_text(encoding="utf-8"))
    await page.wait_for_function("document.querySelector('#source-indicator')?.textContent.includes('Verifierat EQ Timing')")
    return page

async def main():
    race=DATA["data/races/2026-trail43.json"]
    candidates=[];numbers=set()
    for row in race["results"]:
        if row["status"]=="FINISHED" and row.get("bib") and row["bib"] not in numbers:
            candidates.append(row);numbers.add(row["bib"])
        if len(candidates)==5:break
    assert len(candidates)==5,"Five public finishers needed for the 2–5 share test"
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(headless=True)
        try:
            page=await new_page(browser)
            assert "43 km · 2026" in await page.locator("#race-title").inner_text()
            assert await page.locator("#share-map-duel-selection").is_disabled()
            async def choose(record):
                await page.locator("#map-duel-search").fill(str(record["bib"]))
                await page.locator('#map-duel-suggestions [data-map-duel-id="'+record["id"]+'"]').click()
            await choose(candidates[0])
            assert await page.locator("#share-map-duel-selection").is_disabled()
            await choose(candidates[1])
            await page.locator("#share-map-duel-selection").click()
            await page.wait_for_function("window.__copiedMapDuel!==null")
            link2=await page.evaluate("window.__copiedMapDuel")
            state2=parse_qs(urlsplit(link2).fragment)
            assert state2["mapDuel"]==[x["id"] for x in candidates[:2]]
            assert state2["family"]==["trail43"] and state2["year"]==["2026"]
            assert not any(x["name"] in link2 for x in candidates[:2])
            assert "Länken är kopierad" in await page.locator("#map-duel-share-status").inner_text()
            for record in candidates[2:]:
                await choose(record)
            assert await page.locator("#map-duel-counter").inner_text()=="5"
            await page.locator("#open-map-duel").click()
            assert await page.locator("#map-duel-dialog").evaluate("(d)=>d.open")
            assert await page.locator("#map-duel-leaderboard tbody tr").count()==5
            await page.locator("#map-duel-clock").evaluate("""el=>{
               el.value='3600';el.dispatchEvent(new Event('input',{bubbles:true}));
            }""")
            await page.evaluate("window.__copiedMapDuel=null")
            await page.locator("#map-duel-share").click()
            await page.wait_for_function("window.__copiedMapDuel?.includes('mapDuelTime=')")
            link5=await page.evaluate("window.__copiedMapDuel")
            state5=parse_qs(urlsplit(link5).fragment)
            assert state5["mapDuel"]==[x["id"] for x in candidates]
            assert state5["mapDuelTime"]==["3600"]
            assert "Länken är kopierad" in await page.locator("#map-duel-modal-share-status").inner_text()
            assert await page.locator("#map-duel-dialog").evaluate("(d)=>d.scrollWidth<=d.clientWidth+1")
            restored=await new_page(browser,link5)
            await restored.wait_for_function("document.querySelector('#map-duel-dialog')?.open===true")
            assert await restored.locator("#map-duel-counter").inner_text()=="5"
            assert await restored.locator("#map-duel-leaderboard tbody tr").count()==5
            assert int(await restored.locator("#map-duel-clock").input_value())==3600
            assert await restored.locator("#map-duel-play").inner_text()=="Spela"
            await restored.close()
            # A link from the wrong edition may never silently show unrelated runners.
            parsed=urlsplit(link5)
            wrong=parse_qs(parsed.fragment)
            wrong["family"]=["trail22"];wrong["year"]=["2024"]
            wrong_url=urlunsplit((parsed.scheme,parsed.netloc,parsed.path,parsed.query,urlencode(wrong,doseq=True)))
            wrong_page=await new_page(browser,wrong_url)
            assert "22 km · 2024" in await wrong_page.locator("#race-title").inner_text()
            assert not await wrong_page.locator("#map-duel-dialog").evaluate("(d)=>d.open")
            await wrong_page.close()
            await page.locator('[data-close="map-duel-dialog"]').click()
            await page.locator("[data-remove-map-duel]").first.click()
            assert "mapDuel=" not in page.url, "Changing the selected group must invalidate old share state"
            await page.close()
            print("PASS shareable 2 and 5 runner Kartduell, copied URL, pause time, restore and rejection",flush=True)
        finally:await browser.close()

if __name__=="__main__":asyncio.run(main())
