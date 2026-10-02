#!/usr/bin/env python3
"""Real Chromium map coverage on all seven historically verified ultra85 years."""
import asyncio,json,os,re
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(os.getenv("SATILA_SITE","docs"))
YEARS=(2018,2019,2021,2022,2023,2024,2025)
async def main():
 catalog=json.loads((ROOT/"data/bootstrap.json").read_text(encoding="utf-8"))
 editions={e["race_key"]:e for e in catalog["editions"]}
 fixtures={}
 for p in (ROOT/"data").glob("*.json"):fixtures["data/"+p.name]=json.loads(p.read_text(encoding="utf-8"))
 for p in (ROOT/"data/races").glob("*.json"):fixtures["data/races/"+p.name]=json.loads(p.read_text(encoding="utf-8"))
 for p in (ROOT/"data/routes").glob("*.json"):fixtures["data/routes/"+p.name]=json.loads(p.read_text(encoding="utf-8"))
 markup=(ROOT/"index.html").read_text(encoding="utf-8")
 markup=re.sub(r"<link [^>]*>","",markup)
 markup=re.sub(r"<script[^>]*>\s*</script>","",markup)
 app=(ROOT/"assets/app.js").read_text(encoding="utf-8")
 async with async_playwright() as pw:
  opts={"headless":True}
  if Path("/usr/bin/chromium").exists():opts.update(executable_path="/usr/bin/chromium",args=["--no-sandbox"])
  browser=await pw.chromium.launch(**opts)
  try:
   for width,height in ((1440,900),(390,844)):
    page=await browser.new_page(viewport={"width":width,"height":height})
    page.set_default_timeout(12000)
    errors=[];page.on("pageerror",lambda e:errors.append(str(e)))
    await page.set_content(markup)
    await page.add_style_tag(content=(ROOT/"assets/style.css").read_text(encoding="utf-8"))
    await page.add_style_tag(content=(ROOT/"assets/style-extra.css").read_text(encoding="utf-8"))
    await page.evaluate("""data=>{
       window.__fixtures=data;window.__missing=[];
       window.fetch=async url=>{
        const v=window.__fixtures[String(url)];
        if(v===undefined)window.__missing.push(String(url));
        return {ok:v!==undefined,status:v===undefined?404:200,json:async()=>v};
       };
    }""",fixtures)
    await page.add_script_tag(content=app)
    await page.wait_for_function("document.querySelector('#source-indicator').textContent.includes('Verifierat EQ Timing')")
    await page.locator('[data-family="ultra85"]').click()
    for year in YEARS:
     edition=editions[f"{year}-ultra85"]
     route=fixtures["data/"+edition["route_file"]]
     await page.locator("#year-select").select_option(str(year))
     await page.wait_for_function("""p=>{
      let t=document.querySelector('#race-title')?.textContent||'';
      let hit=document.querySelector('#course-map [data-map-hit]');
      return t.includes(String(p.year))&&hit&&Math.abs(Number(hit.getAttribute('aria-valuemax'))-p.km)<.001;
     }""",arg={"year":year,"km":route["geometry_length_km"]})
     assert await page.locator("#course-map .route-base").count()==1,(width,year,"map absent")
     assert await page.locator("#course-map [data-map-hit]").count()==1,(width,year,"course scrub absent")
     assert "Höjddata saknas" in await page.locator("#course-elevation").inner_text(),(width,year,"fabricated height?")
     assert await page.locator("#course-elevation .elev-line").count()==0,(width,year,"fabricated height chart")
     label=await page.locator("#course-map .map-label").first.text_content()
     assert ("TRACE DE TRAIL" in label if year==2022 else "DELTAGARSPÅR" in label),(width,year,label)
     assert await page.locator("#results-table tbody tr").count()>0,(width,year,"results missing")
     overflow=await page.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
     assert overflow<=1,(width,year,"horizontal overflow",overflow)
     print(f"PASS {width}px ultra85 {year}: {len(route['points'])} real route display points, map and missing elevation disclosed",flush=True)
    for year in (2016,2017):
     await page.locator("#year-select").select_option(str(year))
     await page.wait_for_function("""y=>document.querySelector('#race-title').textContent.includes(String(y))
       && !document.querySelector('#course-map [data-map-hit]')""",arg=year)
     assert not editions[f"{year}-ultra85"].get("route_file"),year
    assert not errors,(width,errors)
    assert not await page.evaluate("window.__missing"),(width,await page.evaluate("window.__missing"))
    await page.close()
  finally:await browser.close()
 print("PASS all seven ultra85 historical maps + two unlinked older years desktop/mobile",flush=True)
if __name__=="__main__":asyncio.run(main())
