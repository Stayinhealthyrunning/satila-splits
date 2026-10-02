#!/usr/bin/env python3
"""Browser acceptance: every owner-supplied 43 km year shows its linked map.
A route is independently available from partial EQ Timing observations.
"""
from __future__ import annotations
import asyncio,collections,json,os,re
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path(os.getenv("SATILA_SITE","docs"))
YEARS=(2021,2022,2023,2024,2025)

async def main():
    boot=json.loads((ROOT/"data/bootstrap.json").read_text(encoding="utf-8"))
    editions={e["race_key"]:e for e in boot["editions"]}
    fixtures={}
    for p in (ROOT/"data").glob("*.json"):
        fixtures["data/"+p.name]=json.loads(p.read_text(encoding="utf-8"))
    for p in (ROOT/"data/races").glob("*.json"):
        fixtures["data/races/"+p.name]=json.loads(p.read_text(encoding="utf-8"))
    for p in (ROOT/"data/routes").glob("*.json"):
        fixtures["data/routes/"+p.name]=json.loads(p.read_text(encoding="utf-8"))
    expected={2021:1090,2022:1090,2023:822,2024:1018,2025:1380}
    for year in YEARS:
        edition=editions[f"{year}-trail43"]
        route=fixtures["data/"+edition["route_file"]]
        assert len(route["points"])==expected[year],(year,"Wrong or missing route geometry")
        if year<2025:
            assert route["edition_references"]==[year],(year,"Wrong year route")
            assert route["type"]=="VERIFIED_PARTICIPANT"
        else:
            assert route["type"]=="OFFICIAL_ORGANIZER"
        if year in (2021,2022,2023):
            assert route["normalized_source_group"]==("trail43-2021-2022-normalized" if year<=2022 else "trail43-2023-2025-normalized")
    markup=(ROOT/"index.html").read_text(encoding="utf-8")
    markup=re.sub(r"<link [^>]*>","",markup)
    markup=re.sub(r"<script[^>]*>\s*</script>","",markup)
    app=(ROOT/"assets/app.js").read_text(encoding="utf-8")
    base_css=(ROOT/"assets/style.css").read_text(encoding="utf-8")
    extra_css=(ROOT/"assets/style-extra.css").read_text(encoding="utf-8")
    async with async_playwright() as p:
        opts={"headless":True}
        if Path("/usr/bin/chromium").exists():
            opts.update(executable_path="/usr/bin/chromium",args=["--no-sandbox"])
        browser=await p.chromium.launch(**opts)
        for width in (1440,390):
            page=await browser.new_page(viewport={"width":width,"height":900 if width>390 else 844})
            errors=[]
            page.on("pageerror",lambda error:errors.append(str(error)))
            await page.set_content(markup)
            await page.add_style_tag(content=base_css)
            await page.add_style_tag(content=extra_css)
            await page.evaluate("""data=>{
              window.__fixtures=data;window.__missing=[];
              window.fetch=async url=>{
                const val=window.__fixtures[String(url)];
                if(val===undefined)window.__missing.push(String(url));
                return {ok:val!==undefined,status:val===undefined?404:200,json:async()=>val};
              };
            }""",fixtures)
            await page.add_script_tag(content=app)
            await page.wait_for_function("document.querySelector('#race-title').textContent.includes('2025')")
            for year in YEARS:
                await page.locator("#year-select").select_option(str(year))
                route=fixtures["data/"+editions[f"{year}-trail43"]["route_file"]]
                await page.wait_for_function(
                    """p=>document.querySelector('#race-title').textContent.includes(''+p.year)
                      && document.querySelector('#course-map [data-map-hit]')
                      && Math.abs(Number(document.querySelector('#course-map [data-map-hit]').getAttribute('aria-valuemax'))-p.length)<.001""",
                    arg={"year":year,"length":route["geometry_length_km"]})
                assert await page.locator("#course-map .route-base").count()==1,(width,year,"map missing")
                assert await page.locator("#course-elevation .elev-line").count()==1,(width,year,"elevation missing")
                assert await page.locator("#course-map [data-map-hit]").count()==1,(width,year,"map seek missing")
                assert await page.locator("#course-elevation [data-elev-hit]").count()==1,(width,year,"elevation seek missing")
                label=await page.locator("#course-map .map-label").first.text_content()
                note=await page.locator("#course-source").text_content()
                if year in (2021,2022,2023):
                    assert "NORMALISERAD DELTAGARBANA" in label,(width,year,label)
                    assert "Normaliserad deltagarbaserad bana" in note,(width,year,note)
                elif year==2024:
                    assert "DELTAGARSPÅR" in label,(width,year,label)
                else:
                    assert "ARRANGÖRSRUTT" in label,(width,year,label)
                route=fixtures["data/"+editions[f"{year}-trail43"]["route_file"]]
                length=float(await page.locator("#course-map [data-map-hit]").get_attribute("aria-valuemax"))
                assert abs(length-route["geometry_length_km"])<.001,(width,year,length)
                print(f"PASS {width}px {year}/43: {len(route['points'])} source-derived map points, labels and elevation",flush=True)
            assert not await page.evaluate("window.__missing"),(width,await page.evaluate("window.__missing"))
            assert not errors,(width,errors)
            await page.close()
        await browser.close()
    print("PASS: all 2021–2025 year-scoped 43km map/elevation displays in desktop and mobile")

if __name__=="__main__":asyncio.run(main())
