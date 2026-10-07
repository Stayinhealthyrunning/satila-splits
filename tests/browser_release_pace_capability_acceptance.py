#!/usr/bin/env python3
"""Release-only browser acceptance for pace-distance capability gating.

2023 and 2024 trail43 have known timing-km metadata anomalies at Torrås -> Almered.
The 2019 and 2021 ultra editions also have an 82 km EQ Timing axis but an
organizer-advertised 85 km distance. Their year-specific participant geometry
is kept distinct from both values and enables explicitly sourced display and
whole-course pace without changing any official TIME observation.
"""
import asyncio,json,os,re,statistics
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path(os.getenv("SATILA_SITE","docs"))

def display_time(seconds):
    value=round(seconds)
    hours,remainder=divmod(value,3600)
    minutes,secs=divmod(remainder,60)
    return f"{hours}:{minutes:02d}:{secs:02d}"

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
    profile_js=(ROOT/"assets/profile-analysis.js").read_text(encoding="utf-8")
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
            await page.add_script_tag(content=profile_js)
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

            await page.locator('[data-family="ultra85"]').click()
            for year in ("2019","2021"):
                await page.locator("#year-select").select_option(year)
                await page.wait_for_function("(y)=>document.querySelector('#race-title').textContent.includes('85 km · '+y)",arg=year)
                await page.wait_for_timeout(150)
                option_text=await page.locator(f'#year-select option[value="{year}"]').inner_text()
                assert "85 km" in option_text and "82 km" not in option_text,option_text
                race=fixtures[f"data/races/{year}-ultra85.json"]
                expected=display_time(statistics.median(row["finish_seconds"] for row in race["results"] if row["status"]=="FINISHED" and row.get("finish_seconds",0)>0))
                assert await page.locator("#target-time").input_value()==expected
                assert await page.locator("#target-time").get_attribute("data-default-source")=="edition-median"
                intel=(await page.locator("#course-intelligence").inner_text()).replace("\n"," ")
                assert "EQ Timing-distans 82,0 km" in intel,intel
                assert "Arrangörsdistans 85,0 km" in intel,intel
                pacing=(await page.locator("#segment-pacing").inner_text()).lower()
                assert "eget hel-loppssnitt" in pacing,pacing
                result_row=page.locator("#results-table tbody tr").first
                row_text=(await result_row.inner_text()).replace("\n"," ")
                assert "85,0 km annonserat" in row_text and "EQ Timing 82,0 km" in row_text,row_text
                await result_row.locator("button[data-open]").click()
                profile=(await page.locator("#profile-content").inner_text()).replace("\n"," ")
                assert "Snittfart" in profile and "Distanskonflikt" not in profile,profile
                assert "Helbanetempo visas inte" not in profile,profile
                await page.locator('[data-close="profile-dialog"]').click()
                assert await page.locator("#course-map svg").count()==1
                intel=(await page.locator("#course-intelligence").inner_text()).replace("\n"," ")
                assert "Verifierat deltagarspår · endast display" in intel,intel
                assert "Höjddata saknas i källspåret" in intel,intel
                assert "NaN" not in intel,intel
                print("RELEASE DISTANCE-SEMANTICS ACCEPTANCE PASSED",year,flush=True)
        finally:
            await browser.close()

if __name__=="__main__":
    asyncio.run(main())
