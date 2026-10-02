#!/usr/bin/env python3
"""Acceptance coverage for the seven owner requested prepublication UI changes."""
import asyncio,json,os,re,statistics
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path(os.getenv("SATILA_SITE","docs"))
OUT=Path(os.getenv("SATILA_QA_OUTPUT","/tmp/satila-prepublish-qa"))
OUT.mkdir(parents=True,exist_ok=True)

def fixtures():
    boot=json.loads((ROOT/"data/bootstrap.json").read_text(encoding="utf-8"))
    data={"data/bootstrap.json":boot,"data/coverage.json":json.loads((ROOT/"data/coverage.json").read_text(encoding="utf-8"))}
    for edition in boot["editions"]:
        path=ROOT/"data/races"/f"{edition['race_key']}.json"
        data[f"data/races/{path.name}"]=json.loads(path.read_text(encoding="utf-8"))
    for path in (ROOT/"data/routes").glob("*.json"):
        data[f"data/routes/{path.name}"]=json.loads(path.read_text(encoding="utf-8"))
    return data

def fmt_time(seconds):
    seconds=round(seconds);hours=seconds//3600;minutes=seconds%3600//60;secs=seconds%60
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"

async def build_page(browser,data,markup,script,width,height,url="http://satila.test/"):
    page=await browser.new_page(viewport={"width":width,"height":height})
    page.set_default_timeout(10000)
    errors=[];page.on("pageerror",lambda error:errors.append(str(error)))
    async def serve(route):await route.fulfill(status=200,content_type="text/html",body=markup)
    await page.route("http://satila.test/**",serve)
    await page.goto(url,wait_until="domcontentloaded")
    await page.add_style_tag(content=(ROOT/"assets/style.css").read_text(encoding="utf-8"))
    await page.add_style_tag(content=(ROOT/"assets/style-extra.css").read_text(encoding="utf-8"))
    await page.evaluate("""payload=>{
      window.__fixtures=payload;window.__missing=[];
      window.fetch=async url=>{const value=window.__fixtures[String(url)];if(value===undefined)window.__missing.push(String(url));return {ok:value!==undefined,status:value===undefined?404:200,json:async()=>value}}
    }""",data)
    await page.add_script_tag(content=script)
    return page,errors

async def main():
    data=fixtures()
    markup=(ROOT/"index.html").read_text(encoding="utf-8")
    markup=re.sub(r"<link [^>]*>","",markup)
    markup=re.sub(r"<script[^>]*>\s*</script>","",markup)
    script=(ROOT/"assets/app.js").read_text(encoding="utf-8")
    race=data["data/races/2025-trail43.json"]
    finish=[r["finish_seconds"] for r in race["results"] if r["status"]=="FINISHED" and r.get("finish_seconds",0)>0]
    expected_mean=fmt_time(statistics.mean(finish))
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(headless=True)
        try:
            # Explicit query deep links still win over the 43 km default.
            linked,linked_errors=await build_page(browser,data,markup,script,900,900,"http://satila.test/?family=ultra85&year=2024")
            await linked.wait_for_function("document.querySelector('#race-title')?.textContent.includes('85 km · 2024')")
            assert not linked_errors,linked_errors
            await linked.close()

            for width,height in ((1440,900),(900,900),(768,900),(390,844)):
                page,errors=await build_page(browser,data,markup,script,width,height)
                await page.wait_for_function("document.querySelector('#race-title')?.textContent.includes('43 km · 2025')")

                # 1–2: default latest 43 km and real arithmetic FINISHED mean.
                assert await page.locator("#goal-placement-time").input_value()==expected_mean
                assert await page.locator("#goal-placement-time").get_attribute("data-default-source")=="finished-mean"
                assert "aritmetiskt medel" in (await page.locator("#goal-placement").inner_text()).lower()

                # 3: exactly the four requested field status summaries.
                labels=await page.locator("#status-chart .status-summary article>span").all_text_contents()
                assert labels==["Anmälda","Startande","DNF","Fullföljt"],(width,labels)
                values=[int(v.replace("\xa0","")) for v in await page.locator("#status-chart .status-summary article>strong").all_text_contents()]
                expected=[len(race["results"]),sum(r["status"]!="DNS" for r in race["results"]),sum(r["status"]=="DNF" for r in race["results"]),len(finish)]
                assert values==expected,(width,values,expected)

                # 4: obsolete DNF panel is absent and placement owns the full row.
                assert await page.locator("#dnf-chart").count()==0
                assert await page.locator(".placement-wide #placement-chart").count()==1

                # 5: five switchable lists, with women and men kept side by side.
                tabs=page.locator("#standouts [data-standout-tab]")
                assert await tabs.count()==5
                await tabs.nth(2).click()
                assert await tabs.nth(2).get_attribute("aria-selected")=="true"
                groups=page.locator("#standouts .standout-active .podium-group")
                assert await groups.count()==2
                boxes=[await groups.nth(i).bounding_box() for i in range(2)]
                assert boxes[1]["x"]>boxes[0]["x"] and abs(boxes[1]["y"]-boxes[0]["y"])<3,(width,boxes)

                # 6: independent start/end controls only expose forward ranges.
                start=page.locator("#podium-segment-start");end=page.locator("#podium-segment-end")
                assert await start.count()==await end.count()==1
                await start.select_option("1")
                await page.wait_for_function("document.querySelector('#podium-segment-start')?.value==='1'")
                end_values=await end.locator("option").evaluate_all("nodes=>nodes.map(node=>Number(node.value))")
                assert end_values and all(value>1 for value in end_values),(width,end_values)
                await end.select_option(str(end_values[-1]))
                assert "giltiga tidspar" in await page.locator("#segment-podium .segment-range-summary").inner_text()
                assert await page.locator("#segment-podium .podium-group").count()==2

                # 7: the main geographic map has real OSM tile images and attribution.
                assert await page.locator("#course-map .osm-tile-layer image").count()>0
                # Real OSM imagery must cover the full SVG viewBox, not only the
                # route bounding box; long thin tracks previously had grey strips.
                tile_coverage=await page.locator("#course-map").evaluate("""host=>{
                  const svg=host.querySelector('svg'),layer=svg.querySelector('.osm-tile-layer'),
                    images=Array.from(layer.querySelectorAll('image')),view=svg.viewBox.baseVal;
                  const minX=Math.min(...images.map(img=>img.x.baseVal.value)),
                    minY=Math.min(...images.map(img=>img.y.baseVal.value)),
                    maxX=Math.max(...images.map(img=>img.x.baseVal.value+img.width.baseVal.value)),
                    maxY=Math.max(...images.map(img=>img.y.baseVal.value+img.height.baseVal.value));
                  return {full:minX<=view.x+1 && minY<=view.y+1 &&
                    maxX>=view.x+view.width-1 && maxY>=view.y+view.height-1,
                    tileCount:images.length,zoom:Number(layer.dataset.zoom)};
                }""")
                # A fixed 800:340 aspect ratio can hide OSM sidebars at the
                # expense of an unusably short mobile map. Preserve the
                # original responsive panel height and match its SVG viewBox.
                panel_height=await page.locator("#course-map").evaluate("(el)=>el.getBoundingClientRect().height")
                assert panel_height >= (210 if width==390 else 330),(width,"responsive OSM map too shallow",panel_height)
                assert tile_coverage["full"],(width,"OSM side strips",tile_coverage)
                assert 1<=tile_coverage["tileCount"]<=24,(width,"OSM tile budget",tile_coverage)
                assert 8<=tile_coverage["zoom"]<=15,(width,"OSM tile zoom",tile_coverage)
                attribution=page.locator("#course-map .osm-attribution")
                assert "OpenStreetMap" in await attribution.inner_text()
                assert await attribution.get_attribute("href")=="https://www.openstreetmap.org/copyright"

                overflow=await page.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
                assert overflow<=1,(width,overflow)
                assert not errors,(width,errors)
                assert not await page.evaluate("window.__missing||[]"),(width,await page.evaluate("window.__missing||[]"))
                await page.screenshot(path=str(OUT/f"satila-prepublish-{width}.png"),full_page=True,animations="disabled")
                await page.locator("#dynamics").screenshot(path=str(OUT/f"satila-prepublish-dynamics-{width}.png"),animations="disabled")
                await page.locator("#segments").screenshot(path=str(OUT/f"satila-prepublish-segments-{width}.png"),animations="disabled")
                await page.locator("#course-map").screenshot(path=str(OUT/f"satila-prepublish-map-{width}.png"),animations="disabled")

                if width==1440:
                    # 2021 22 km has one UNKNOWN record with no public TIME.
                    # Excluding only DNS would incorrectly claim this person started.
                    await page.evaluate("location.hash='#family=trail22&year=2021'")
                    await page.wait_for_function("document.querySelector('#race-title')?.textContent.includes('22 km · 2021')")
                    await page.wait_for_function("""() => document.querySelector('#year-select')?.value==='2021' &&
                        document.querySelector('#status-chart .status-summary article strong')?.textContent.trim()==='217'""")
                    historic=data["data/races/2021-trail22.json"]["results"]
                    assert sum(r["status"]=="UNKNOWN" for r in historic)==1
                    historic_values=[int(v.replace("\\xa0","")) for v in await page.locator("#status-chart .status-summary article>strong").all_text_contents()]
                    known_starters=sum(r["status"] in ("FINISHED","DNF","DSQ") for r in historic)
                    expected_historic=[
                        len(historic),known_starters,
                        sum(r["status"]=="DNF" for r in historic),
                        sum(r["status"]=="FINISHED" for r in historic)
                    ]
                    assert historic_values==expected_historic,("UNKNOWN is not a verified starter",historic_values,expected_historic)
                    await page.locator("#dynamics .info").first.click()
                    help_text=await page.locator("#help-content").inner_text()
                    assert "okänd status räknas inte som bekräftad start" in help_text,help_text
                    await page.locator('#help-dialog [data-close="help-dialog"]').click()
                    await page.evaluate("location.hash='#family=trail22&year=2024'")
                    await page.wait_for_function("document.querySelector('#race-title')?.textContent.includes('22 km · 2024')")
                    await page.wait_for_function("document.querySelector('#year-select')?.value==='2024'")
                    # Clicking an ordinary anchor like #dynamics must NOT reset
                    # the chosen historical edition to the latest available year.
                    await page.locator('#primary-nav a[href="#dynamics"]').click()
                    await page.wait_for_timeout(300)
                    assert await page.locator("#year-select").input_value()=="2024",("navigation anchor reset selected year",width)
                    assert "22 km · 2024" in await page.locator("#race-title").inner_text()
                print("PASS prepublish polish",width,height,"overflow",overflow,flush=True)
                await page.close()
        finally:
            await browser.close()

if __name__=="__main__":asyncio.run(main())
