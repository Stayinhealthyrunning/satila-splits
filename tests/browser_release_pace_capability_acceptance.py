#!/usr/bin/env python3
"""Release-only browser acceptance for pace-distance capability gating.

2023 and 2024 trail43 have known timing-km metadata anomalies at Torrås -> Almered.
TIME is valid and must remain visible; pace/min-km must be withheld or clearly
marked non-physical/unverified until segment distance is independently verified.
"""
import asyncio,json,os,re
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path(os.getenv("SATILA_SITE","docs"))

async def main():
    boot=json.loads((ROOT/"data/bootstrap.json").read_text(encoding="utf-8"))
    fixtures={"data/bootstrap.json":boot}
    for ed in boot["editions"]:
        p=ROOT/"data/races"/f"{ed['race_key']}.json"
        fixtures["data/races/"+p.name]=json.loads(p.read_text(encoding="utf-8"))
    for p in (ROOT/"data/routes").glob("*.json"):
        fixtures["data/routes/"+p.name]=json.loads(p.read_text(encoding="utf-8"))

    markup=(ROOT/"index.html").read_text(encoding="utf-8")
    markup=re.sub(r"<link [^>]*>","",markup)
    markup=re.sub(r"<script[^>]*>\s*</script>","",markup)
    js=(ROOT/"assets/app.js").read_text(encoding="utf-8")

    async with async_playwright() as pw:
        browser=await pw.chromium.launch(headless=True)
        try:
            page=await browser.new_page(viewport={"width":1440,"height":900})
            await page.set_content(markup)
            await page.add_style_tag(content=(ROOT/"assets/style.css").read_text(encoding="utf-8"))
            extra=ROOT/"assets/style-extra.css"
            if extra.exists(): await page.add_style_tag(content=extra.read_text(encoding="utf-8"))
            await page.evaluate("""d=>{
              window.__fixtures=d;
              window.fetch=async u=>{
                const x=window.__fixtures[String(u)];
                return {ok:x!==undefined,status:x===undefined?404:200,json:async()=>x};
              };
            }""",fixtures)
            await page.add_script_tag(content=js)
            await page.wait_for_function("document.querySelector('#race-title').textContent.includes('2025')")
            await page.locator('[data-family="trail43"]').click()
            for year in ("2023","2024"):
                await page.locator("#year-select").select_option(year)
                await page.wait_for_function("(y)=>document.querySelector('#race-title').textContent.includes('43 km · '+y)",arg=year)

                rows=page.locator("#segment-table tbody tr")
                target=None
                for i in range(await rows.count()):
                    cells=await rows.nth(i).locator("td").all_text_contents()
                    if cells and "Torrås" in cells[0] and "Almered" in cells[0]:
                        target=cells
                        break
                assert target is not None,f"Known {year} Torrås→Almered segment missing"
                # Median TIME must remain usable.
                assert target[3].strip() not in ("","—","-"),target
                # Pace must be unavailable OR explicitly qualified as unverified/time-only.
                pace=target[5].strip().lower() if len(target)>5 else ""
                qualified=(
                    pace in ("","—","-","ej verifierad","saknas") or
                    any(token in pace for token in ("tid-only","tid endast","distans ej verifierad","ej verifierad"))
                )
                assert qualified,(
                    f"{year} questionable timing-km segment still exposes unqualified pace/min-km",
                    target
                )
                # The same distance rule applies to a runner's PERSONAL segment
                # table, not only the aggregate lab. Select an actual finisher
                # with the two published TIME readings, through the real search UI.
                race=fixtures[f"data/races/{year}-trail43.json"]
                torras=next(x["uid"] for x in race["stations"] if x["name"]=="Torrås")
                almered=next(x["uid"] for x in race["stations"] if x["name"]=="Almered")
                actual={}
                for observation in race["splits"]:
                    if observation["station_uid"] in (torras,almered):
                        actual.setdefault(observation["result_id"],{})[observation["station_uid"]]=observation["elapsed_seconds"]
                candidates=[r for r in race["results"]
                            if r["status"]=="FINISHED" and r.get("name") and
                            torras in actual.get(r["id"],{}) and almered in actual.get(r["id"],{}) and
                            actual[r["id"]][almered]>actual[r["id"]][torras]]
                assert candidates,f"No actual {year} runner with both published anchors"
                selected=None
                for candidate in candidates[:30]:
                    await page.locator("#runner-search").fill(candidate["name"])
                    choices=page.locator("#runner-suggestions .suggestion")
                    for index in range(await choices.count()):
                        if await choices.nth(index).get_attribute("data-id")==str(candidate["id"]):
                            await choices.nth(index).click()
                            selected=candidate
                            break
                    if selected:break
                assert selected,f"Cannot select a real {year} runner through UI"
                assert await page.locator("#profile-dialog").evaluate("d=>d.open")
                tables=page.locator("#profile-content table")
                assert await tables.count()>=2
                matched=None
                for row in await tables.nth(1).locator("tbody tr").all():
                    fields=await row.locator("td").all_text_contents()
                    if fields and "Torrås" in fields[0] and "Almered" in fields[0]:
                        matched=fields
                        break
                assert matched,f"Personal {year} suspect segment missing"
                assert matched[2].strip() not in ("","—","-"),matched
                assert "distans ej verifierad" in matched[3].lower(),(
                    f"Personal {year} profile still exposes unjustified physical min/km",
                    matched
                )
                await page.locator('[data-close="profile-dialog"]').click()
                print("RELEASE PACE-CAPABILITY ACCEPTANCE PASSED",year,"aggregate and profile",flush=True)
        finally:
            await browser.close()

if __name__=="__main__":
    asyncio.run(main())
