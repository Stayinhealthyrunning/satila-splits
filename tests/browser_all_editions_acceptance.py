#!/usr/bin/env python3
"""Offline Chromium coverage: every public Sätila RaceEdition on desktop/mobile."""
import asyncio,json,os,re
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(os.getenv("SATILA_SITE","docs"))

async def main():
    catalog=json.loads((ROOT/"data/bootstrap.json").read_text(encoding="utf-8"))
    assert len(catalog["editions"])==27
    fixtures={"data/bootstrap.json":catalog}
    for ed in catalog["editions"]:
        path=ROOT/"data/races"/(ed["race_key"]+".json")
        fixtures["data/races/"+path.name]=json.loads(path.read_text(encoding="utf-8"))
    for path in (ROOT/"data/routes").glob("*.json"):
        fixtures["data/routes/"+path.name]=json.loads(path.read_text(encoding="utf-8"))
    # Codex's coverage dashboard loads an additional valid public root JSON.
    # Load ALL committed root manifests rather than hiding missing fetches.
    for manifest in (ROOT/"data").glob("*.json"):
        fixtures["data/"+manifest.name]=json.loads(manifest.read_text(encoding="utf-8"))
    markup=(ROOT/"index.html").read_text(encoding="utf-8")
    markup=re.sub(r"<link [^>]*>","",markup)
    markup=re.sub(r"<script[^>]*>\s*</script>","",markup)
    js=(ROOT/"assets/app.js").read_text(encoding="utf-8")
    opts={"headless":True}
    if Path("/usr/bin/chromium").exists():
        opts.update(executable_path="/usr/bin/chromium",args=["--no-sandbox"])
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(**opts)
        try:
            for width,height in ((1440,900),(390,844)):
                page=await browser.new_page(viewport={"width":width,"height":height})
                page.set_default_timeout(7000)
                errors=[]
                page.on("pageerror",lambda e:errors.append(str(e)))
                await page.set_content(markup)
                await page.add_style_tag(content=(ROOT/"assets/style.css").read_text(encoding="utf-8"))
                extra=ROOT/"assets/style-extra.css"
                if extra.exists():
                    await page.add_style_tag(content=extra.read_text(encoding="utf-8"))
                await page.evaluate("""data=>{
                  window.__fixtures=data;
                  window.fetch=async url=>{
                    const x=window.__fixtures[String(url)];
                    if(x===undefined)(window.__missing??=[]).push(String(url));
                    return {ok:x!==undefined,status:x===undefined?404:200,json:async()=>x};
                  };
                }""",fixtures)
                await page.add_script_tag(content=js)
                await page.wait_for_function("document.querySelector('#source-indicator').textContent.includes('Verifierat EQ Timing')")
                visited=[]
                for family in ("ultra85","trail43","trail22"):
                    await page.locator('[data-family="'+family+'"]').click()
                    for ed in sorted((e for e in catalog["editions"] if e["family"]==family),key=lambda e:e["year"],reverse=True):
                        await page.locator("#year-select").select_option(str(ed["year"]))
                        await page.wait_for_function("""ed=>{
                          const title=document.querySelector('#race-title').textContent;
                          const source=document.querySelector('#source-indicator').textContent;
                          const scope=document.querySelector('#scope-status').textContent;
                          const link=document.querySelector('#official-source').href;
                          return title.includes(String(ed.year)) &&
                            source.includes('Verifierat EQ Timing') &&
                            source.includes(String(ed.timing_stations)+' stationer') &&
                            link===ed.source_url &&
                            scope.includes(ed.results.toLocaleString('sv-SE'));
                        }""",arg=ed,timeout=15000)
                        assert await page.locator("#segment-table tbody tr").count()>0,(width,ed["race_key"])
                        assert await page.locator("#results-table tbody tr").count()>0,(width,ed["race_key"])
                        present=await page.locator("#course-map svg").count()>0
                        assert present==bool(ed.get("route_file")),(width,ed["race_key"],present,ed.get("route_file"))
                        overflow=await page.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
                        assert overflow<=1,(width,ed["race_key"],overflow)
                        visited.append(ed["race_key"])
                assert len(visited)==len(set(visited))==27,(width,len(visited))
                assert not errors,(width,errors)
                missing=await page.evaluate("window.__missing||[]")
                assert not missing,missing
                print("PASS all 27 public editions, expected checkpoints, routes and UI:",width,height,flush=True)
                await page.close()
        finally:
            await browser.close()

if __name__=="__main__":
    asyncio.run(main())
