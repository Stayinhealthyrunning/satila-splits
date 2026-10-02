#!/usr/bin/env python3
"""Offline real-data Chromium acceptance: map/elevation and H2H scrub on desktop/mobile.

The runner positions are illustrative along the approved organizer GPX. Public
TIME anchors remain source observations; this test never downloads athlete GPS.
"""
import asyncio,json,os,re
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(os.getenv("SATILA_SITE","docs"))
OUT=Path(os.getenv("SATILA_INTERACTION_QA","/tmp/satila-interaction-qa"))
OUT.mkdir(parents=True,exist_ok=True)

def payload():
    boot=json.loads((ROOT/"data/bootstrap.json").read_text(encoding="utf-8"))
    data={"data/bootstrap.json":boot}
    for ed in boot["editions"]:
        p=ROOT/"data/races"/(ed["race_key"]+".json")
        data["data/races/"+p.name]=json.loads(p.read_text(encoding="utf-8"))
    for p in (ROOT/"data/routes").glob("*.json"):
        data["data/routes/"+p.name]=json.loads(p.read_text(encoding="utf-8"))
    # Codex's coverage dashboard loads an additional valid public root JSON.
    # Load ALL committed root manifests rather than hiding missing fetches.
    for manifest in (ROOT/"data").glob("*.json"):
        data["data/"+manifest.name]=json.loads(manifest.read_text(encoding="utf-8"))
    return data

async def position(page,selector):
    return float(await page.locator(selector).get_attribute("aria-valuenow"))

def near(a,b,tolerance=.001):
    assert abs(a-b)<=tolerance,(a,b)

async def main():
    data=payload()
    markup=(ROOT/"index.html").read_text(encoding="utf-8")
    markup=re.sub(r"<link [^>]*>","",markup)
    markup=re.sub(r"<script[^>]*>\s*</script>","",markup)
    js=(ROOT/"assets/app.js").read_text(encoding="utf-8")
    async with async_playwright() as p:
        opts={"headless":True}
        if Path("/usr/bin/chromium").exists():
            opts.update(executable_path="/usr/bin/chromium",args=["--no-sandbox"])
        browser=await p.chromium.launch(**opts)
        try:
            for width,height in ((1440,900),(900,900),(390,844)):
                page=await browser.new_page(viewport={"width":width,"height":height})
                page.set_default_timeout(6000)
                errors=[]
                page.on("pageerror",lambda e:errors.append(str(e)))
                page.on("console",lambda msg:errors.append("console:"+msg.text) if msg.type=="error" else None)
                await page.set_content(markup)
                await page.add_style_tag(content=(ROOT/"assets/style.css").read_text(encoding="utf-8"))
                extra=ROOT/"assets/style-extra.css"
                if extra.exists():await page.add_style_tag(content=extra.read_text(encoding="utf-8"))
                await page.evaluate("""d=>{
                  window.__fixtures=d;
                  window.fetch=async u=>{
                    let x=window.__fixtures[String(u)];
                    if(x===undefined)(window.__missing??=[]).push(String(u));
                    return {ok:x!==undefined,status:x===undefined?404:200,json:async()=>x};
                  };
                }""",data)
                await page.add_script_tag(content=js)
                try:
                    await page.wait_for_function("document.querySelector('#race-title').textContent.includes('2025')")
                except Exception:
                    print("STARTUP_DIAGNOSTICS",width,
                          "title",await page.locator("#race-title").inner_text(),
                          "pageerrors",errors,
                          "missing",await page.evaluate("window.__missing||[]"),flush=True)
                    raise
                await page.locator('[data-family="trail43"]').click()
                await page.wait_for_function("document.querySelector('#race-title').textContent.includes('43 km')")
                # Clicking elevation, then keyboard-operating the map, must update both.
                course_map="#course-map [data-map-hit]"
                course_elev="#course-elevation [data-elev-hit]"
                assert await page.locator(course_map).count()==await page.locator(course_elev).count()==1
                near(await position(page,course_map),0)
                box=await page.locator(course_elev).bounding_box()
                await page.locator(course_elev).click(position={"x":box["width"]*.65,"y":box["height"]*.5})
                distance=await position(page,course_map)
                assert distance>5,(width,distance)
                near(distance,await position(page,course_elev))
                assert "Illustrativ position" in await page.locator("#course-scrub-label").inner_text()
                await page.locator(course_map).focus()
                await page.keyboard.press("ArrowRight")
                advanced=await position(page,course_map)
                assert advanced>distance
                near(advanced,await position(page,course_elev))
                # Independent interaction regression: source-allowed K03
                # segment highlight must NOT intercept clicks on the drawn
                # route. Test the precise overlay stroke, not background space.
                await page.wait_for_function("document.querySelector('#course-map .segment-route-overlay')")
                overlay=page.locator("#course-map .segment-route-overlay")
                assert await overlay.evaluate("(el)=>getComputedStyle(el).pointerEvents")=="none",(
                    width,"segment overlay unexpectedly captures map pointer")
                await page.locator("#course-map").scroll_into_view_if_needed()
                point=await overlay.evaluate("""path=>{
                    const p=path.getPointAtLength(path.getTotalLength()*.5),m=path.getScreenCTM();
                    return {x:m.a*p.x+m.c*p.y+m.e,y:m.b*p.x+m.d*p.y+m.f};
                }""")
                before_overlay=await position(page,course_map)
                await page.mouse.click(point["x"],point["y"])
                after_overlay=await position(page,course_map)
                assert after_overlay>0 and abs(after_overlay-before_overlay)>.01,(
                    width,"route click intercepted by highlighted segment",
                    before_overlay,after_overlay)
                near(after_overlay,await position(page,course_elev))
                # Pick two DIFFERENT real 2025 trail43 finishers via actual UI.
                race=data["data/races/2025-trail43.json"]
                finishers=sorted((r for r in race["results"] if r["status"]=="FINISHED"),key=lambda r:r["finish_seconds"])[:2]
                assert len(finishers)==2 and finishers[0]["id"]!=finishers[1]["id"]
                for runner in finishers:
                    await page.locator("#runner-search").fill(runner["name"])
                    await page.locator("#runner-suggestions .suggestion").first.click()
                    if runner["id"]==finishers[0]["id"]:
                        dialog=page.locator("#profile-dialog")
                        assert await dialog.evaluate("(d)=>d.scrollWidth<=d.clientWidth+1"),(
                            width,"profile dialog has horizontal overflow")
                        assert await dialog.locator("#profile-replay svg").count()>=2
                        await dialog.screenshot(path=str(OUT/f"profile-{width}.png"),animations="disabled")
                    await page.locator("#profile-add-compare").click()
                    await page.locator('[data-close="profile-dialog"]').click()
                assert "(2/2)" in await page.locator("#compare-counter").inner_text()
                await page.locator("#open-compare").click()
                assert await page.locator("#compare-dialog").evaluate("x=>x.open")
                duel_map="#duel-map [data-local-hit]"
                duel_elev="#duel-elevation [data-elev-hit]"
                assert await page.locator(duel_map).count()==await page.locator(duel_elev).count()==1
                box=await page.locator(duel_elev).bounding_box()
                await page.locator(duel_elev).click(position={"x":box["width"]*.72,"y":box["height"]*.5})
                d=await position(page,duel_elev)
                assert d>5
                near(d,await position(page,duel_map))
                near(d,float(await page.locator("#duel-range").input_value()),.051)
                # A real click ON THE DRAWN ROUTE must drive elevation and range.
                point=await page.locator("#duel-map .simple-route-line").evaluate("""path=>{
                  let p=path.getPointAtLength(path.getTotalLength()*.35),m=path.getScreenCTM();
                  return {x:m.a*p.x+m.c*p.y+m.e,y:m.b*p.x+m.d*p.y+m.f};
                }""")
                await page.mouse.click(point["x"],point["y"])
                new=await position(page,duel_map)
                assert new>0 and abs(new-d)>.1,(width,new,d)
                near(new,await position(page,duel_elev))
                near(new,float(await page.locator("#duel-range").input_value()),.051)
                info=await page.locator("#duel-readout").inner_text()
                assert "GPX-distans" in info and "Tidslucka A−B" in info,info
                # A modern 2025 display route must not appear in the 2024 edition.
                compare_dialog=page.locator("#compare-dialog")
                assert await compare_dialog.evaluate("(d)=>d.scrollWidth<=d.clientWidth+1"),(
                    width,"comparison dialog has horizontal overflow")
                await compare_dialog.screenshot(path=str(OUT/f"duel-map-{width}.png"),animations="disabled")
                await compare_dialog.evaluate("(d)=>d.scrollTop=0")
                await compare_dialog.screenshot(path=str(OUT/f"duel-{width}.png"),animations="disabled")
                await page.locator('[data-close="compare-dialog"]').click()
                await page.locator("#year-select").select_option("2024")
                await page.wait_for_function("document.querySelector('#race-title').textContent.includes('2024')")
                assert await page.locator("#course-map svg").count()==0
                assert not errors,(width,errors)
                missing=await page.evaluate("window.__missing||[]")
                assert not missing,missing
                overflow=await page.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
                assert overflow<=1,(width,overflow)
                print("PASS synced map + elevation + H2H real-runner UI:",width,height,flush=True)
                await page.close()
        finally:
            await browser.close()

if __name__=="__main__":
    asyncio.run(main())
