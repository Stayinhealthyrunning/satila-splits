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
    profile_js=(ROOT/"assets/profile-analysis.js").read_text(encoding="utf-8")
    js=(ROOT/"assets/app.js").read_text(encoding="utf-8")
    async with async_playwright() as p:
        opts={"headless":True}
        if Path("/usr/bin/chromium").exists():
            opts.update(executable_path="/usr/bin/chromium",args=["--no-sandbox"])
        browser=await p.chromium.launch(**opts)
        try:
            all_viewports=((1440,900),(900,900),(768,900),(390,844))
            selected={int(value) for value in os.getenv("SATILA_VIEWPORTS","").split(",") if value.strip()}
            viewports=[item for item in all_viewports if not selected or item[0] in selected]
            for width,height in viewports:
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
                await page.add_script_tag(content=profile_js)
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
                # Hover uses the real SVG viewBox, not a fixed CSS width:
                # both edges must map to the ends even on responsive widths.
                box=await page.locator(course_elev).bounding_box()
                await page.locator(course_elev).hover(position={"x":1,"y":box["height"]*.5})
                assert await position(page,course_elev)<.25,(width,"left elevation edge",await position(page,course_elev))
                await page.locator(course_elev).hover(position={"x":box["width"]-1,"y":box["height"]*.5})
                edge=await position(page,course_elev)
                assert edge>float(await page.locator(course_elev).get_attribute("aria-valuemax"))*.98,(width,"right elevation edge",edge)
                await page.locator(course_elev).focus()
                await page.keyboard.press("Home")
                assert await position(page,course_elev)==0
                await page.keyboard.press("End")
                near(await position(page,course_elev),float(await page.locator(course_elev).get_attribute("aria-valuemax")))
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
                sorted_finishers=sorted((r for r in race["results"] if r["status"]=="FINISHED"),key=lambda r:r["finish_seconds"])
                finishers=[sorted_finishers[0],sorted_finishers[-1]]  # Distinct real pacing for common-clock QA.
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
                # Comparison 2.0 analytical order and capability-driven panels.
                assert await page.locator(".comparison-kpis article").count()==9
                section_ids=["comparison-participants","comparison-kpis","comparison-gap","comparison-placement","comparison-segments","comparison-field","comparison-course","comparison-method"]
                tops=[]
                for section_id in section_ids:
                    node=page.locator("#"+section_id)
                    assert await node.count()==1,(width,section_id)
                    tops.append((await node.bounding_box())["y"])
                assert tops==sorted(tops),(width,section_ids,tops)
                assert "positiv = A före" in await page.locator("#comparison-gap").inner_text()
                assert await page.locator("#duel-placement-chart svg").count()==1
                placement_ticks=await page.locator("#duel-placement-chart svg text").evaluate_all(
                    """els=>els.map(el=>({text:el.textContent.trim(),x:Number(el.getAttribute('x')),y:Number(el.getAttribute('y'))}))
                    .filter(item=>Math.abs(item.x-42)<.1&&/^\\d+$/.test(item.text))
                    .sort((a,b)=>a.y-b.y)"""
                )
                assert placement_ticks and placement_ticks[0]["text"]=="1",(width,placement_ticks)
                assert await page.locator(".comparison-segment-table tbody tr").count()>=5
                assert await page.locator("#duel-field-chart svg").count()==1
                assert await page.locator("#duel-duration option").evaluate_all("els=>els.map(x=>x.value)")==["30","60","120","180"]
                assert await page.locator("#duel-duration").input_value()=="120"
                assert await page.locator("#duel-camera").input_value()=="both"
                assert await page.locator("#compare-dialog [data-replay-volume]").input_value()=="0.3"
                await page.locator(".comparison-segment-table [data-duel-segment]").first.click()
                assert await page.locator(".comparison-segment-table tbody tr.selected").count()==1
                # Normal interaction must not rewrite browser history on every
                # clock/segment update. A deep link is materialized only by Share.
                assert "compareA=" not in page.url and "compareB=" not in page.url
                # Both markers MUST use the same elapsed clock, but their own
                # EQ TIME anchor interpolation: fast and slow finisher cannot
                # be tied to the same distance as in the old comparison bug.
                assert await page.locator("#duel-progress-chart svg").count()==1
                assert await page.locator("#duel-clock").count()==1
                await page.locator("#duel-clock").evaluate(
                    "(el,v)=>{el.value=String(v);el.dispatchEvent(new Event('input',{bubbles:true}))}",
                    finishers[0]["finish_seconds"],
                )
                positions=await page.locator("#duel-map [data-runner-marker]").evaluate_all(
                    "els=>els.map(el=>[Number(el.getAttribute('cx')),Number(el.getAttribute('cy'))])"
                )
                assert len(positions)==2
                separation=sum((a-b)**2 for a,b in zip(*positions))**.5
                assert separation>5,(width,positions,separation,"common-clock runners still overlap")
                clock_readout=await page.locator("#duel-readout").inner_text()
                assert "Gemensam tävlingsklocka" in clock_readout
                assert "är cirka" in clock_readout and "km in i loppet" in clock_readout
                assert "Positionsskillnad A−B:" in clock_readout
                assert "Lucka B−A:" in clock_readout
                shared_clock=int(float(await page.locator("#duel-clock").input_value()))
                await page.locator("#duel-share").click()
                shared_hash=await page.evaluate("location.hash")
                assert "compareA=" in shared_hash and "compareB=" in shared_hash,shared_hash
                assert "compareTime=" in shared_hash and "compareSegment=0" in shared_hash,shared_hash
                # At the shared final clock both runners are at the same finish
                # coordinate. The map must not invent a separation for overlap.
                await page.locator("#duel-clock").evaluate(
                    "el=>{el.value=el.max;el.dispatchEvent(new Event('input',{bubbles:true}))}"
                )
                finish_positions=await page.locator("#duel-map [data-runner-marker]").evaluate_all(
                    "els=>els.map(el=>[Number(el.getAttribute('cx')),Number(el.getAttribute('cy'))])"
                )
                assert finish_positions[0]==finish_positions[1],(width,finish_positions,"finish markers must coincide")
                opacities=await page.locator("#duel-map [data-runner-marker]").evaluate_all(
                    "els=>els.map(el=>Number(el.getAttribute('fill-opacity')))"
                )
                assert all(0<opacity<1 for opacity in opacities),(width,opacities,"overlap must remain legible")
                # Return to Start before testing distance-driven map/elevation.
                await page.locator("#duel-reset").click()
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
                assert "position cirka" in info and "Lucka B−A" in info,info
                # A route from another family or edition must not leak into a
                # genuinely route-less historical edition.
                compare_dialog=page.locator("#compare-dialog")
                assert await compare_dialog.evaluate("(d)=>d.scrollWidth<=d.clientWidth+1"),(
                    width,"comparison dialog has horizontal overflow")
                await compare_dialog.screenshot(path=str(OUT/f"duel-map-{width}.png"),animations="disabled")
                await compare_dialog.evaluate("(d)=>d.scrollTop=0")
                await compare_dialog.screenshot(path=str(OUT/f"duel-{width}.png"),animations="disabled")
                await page.locator('[data-close="compare-dialog"]').click()
                await page.locator('[data-family="trail22"]').click()
                await page.wait_for_function("document.querySelector('#race-title').textContent.includes('22 km')")
                assert "compareA=" not in page.url and "compareB=" not in page.url,(width,page.url)
                await page.locator("#year-select").select_option("2024")
                await page.wait_for_function("document.querySelector('#race-title').textContent.includes('2024')")
                assert await page.locator("#course-map svg").count()==0
                assert not errors,(width,errors)
                missing=await page.evaluate("window.__missing||[]")
                assert not missing,missing
                overflow=await page.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
                assert overflow<=1,(width,overflow)
                if width==1440:
                    restored=await browser.new_page(viewport={"width":width,"height":height})
                    restore_errors=[]
                    restored.on("pageerror",lambda e:restore_errors.append(str(e)))
                    restored.on("console",lambda msg:restore_errors.append("console:"+msg.text) if msg.type=="error" else None)
                    await restored.set_content(markup)
                    await restored.add_style_tag(content=(ROOT/"assets/style.css").read_text(encoding="utf-8"))
                    if extra.exists():await restored.add_style_tag(content=extra.read_text(encoding="utf-8"))
                    await restored.evaluate("""d=>{
                      window.__fixtures=d;
                      window.fetch=async u=>{
                        let x=window.__fixtures[String(u)];
                        if(x===undefined)(window.__missing??=[]).push(String(u));
                        return {ok:x!==undefined,status:x===undefined?404:200,json:async()=>x};
                      };
                    }""",data)
                    await restored.evaluate("(hash)=>history.replaceState(null,'',hash)",shared_hash)
                    await restored.add_script_tag(content=profile_js)
                    await restored.add_script_tag(content=js)
                    await restored.wait_for_function("document.querySelector('#compare-dialog')?.open===true")
                    assert "(2/2)" in await restored.locator("#compare-counter").inner_text()
                    assert int(float(await restored.locator("#duel-clock").input_value()))==shared_clock
                    assert await restored.locator(".comparison-segment-table tbody tr.selected").count()==1
                    assert not restore_errors,restore_errors
                    assert not await restored.evaluate("window.__missing||[]")
                    await restored.close()
                print("PASS synced map + elevation + H2H real-runner UI:",width,height,flush=True)
                await page.close()
        finally:
            await browser.close()

if __name__=="__main__":
    asyncio.run(main())
