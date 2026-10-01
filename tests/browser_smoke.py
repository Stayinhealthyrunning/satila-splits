#!/usr/bin/env python3
"""Offline Chromium regression: committed Sätila results, no live EQ requests."""
import asyncio,json,os,re
from collections import Counter
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(os.getenv("SATILA_SITE","docs"))
OUT=Path(os.getenv("SATILA_QA_OUTPUT","/tmp/satila-qa"))
OUT.mkdir(parents=True,exist_ok=True)
async def main():
 b=json.loads((ROOT/"data/bootstrap.json").read_text(encoding="utf-8"))
 assert len(b["editions"])==27 and sum(e["results"] for e in b["editions"])==3272
 data={"data/bootstrap.json":b}
 for e in b["editions"]:
  f=ROOT/"data/races"/(e["race_key"]+".json")
  assert f.is_file(),str(f)
  data["data/races/"+f.name]=json.loads(f.read_text(encoding="utf-8"))
 for f in (ROOT/"data/routes").glob("*.json"):
  data["data/routes/"+f.name]=json.loads(f.read_text(encoding="utf-8"))
 html=(ROOT/"index.html").read_text(encoding="utf-8")
 html=re.sub(r"<link [^>]*>","",html)
 html=re.sub(r"<script[^>]*>\s*</script>","",html)
 css=(ROOT/"assets/style.css").read_text(encoding="utf-8")
 js=(ROOT/"assets/app.js").read_text(encoding="utf-8")
 async with async_playwright() as p:
  opts={"headless":True}
  if Path("/usr/bin/chromium").exists():
   opts.update(executable_path="/usr/bin/chromium",args=["--no-sandbox"])
  browser=await p.chromium.launch(**opts)
  for width,height in [(1440,900),(900,900),(768,900),(390,844)]:
   page=await browser.new_page(viewport={"width":width,"height":height})
   errors=[]
   page.on("pageerror",lambda e:errors.append(str(e)))
   page.on("console",lambda m:errors.append(m.text) if m.type=="error" else None)
   await page.set_content(html)
   await page.add_style_tag(content=css)
   await page.add_style_tag(content=(ROOT/"assets/style-extra.css").read_text(encoding="utf-8"))
   await page.evaluate("""payload=>{
    window.__fixtures=payload;
    window.fetch=async url=>{
     let v=window.__fixtures[String(url)];
     if(v===undefined)window.__missing=(window.__missing||[]).concat([String(url)]);
     return {ok:v!==undefined,status:v===undefined?404:200,json:async()=>v};
    };
   }""",data)
   await page.add_script_tag(content=js)
   try:
    await page.wait_for_function("document.querySelector('#race-title').textContent.includes('2025')",timeout=20000)
   except Exception:
    print("STARTUP_DIAGNOSTICS",width,"title",await page.locator('#race-title').inner_text(),"errors",errors,"missing",await page.evaluate("window.__missing||[]"),flush=True)
    raise
   await page.wait_for_selector("#extra-overview",timeout=20000)
   assert "85 km" in await page.locator("#race-title").inner_text()
   assert await page.locator("#segment-table tbody tr").count()>0
   for ex in ("#extra-overview","#extra-dynamics","#extra-segments","#extra-course","#extra-history","#segment-heatmap","#history-fingerprint","#coverage-table"):
    assert await page.locator(ex).count()==1,(width,ex)
   for family in ("trail43","trail22","ultra85"):
    await page.locator('[data-family="'+family+'"]').click()
    await page.wait_for_function("""f=>document.querySelector('[data-family="'+f+'"]').classList.contains('selected')""",arg=family)
    assert await page.locator("#segment-table tbody tr").count()>0
    if family in ("trail43","trail22"):assert await page.locator("#course-map svg").count()>0
   await page.locator("#year-select").select_option("2016")
   await page.wait_for_function("document.querySelector('#race-title').textContent.includes('2016')")
   assert "Ingen godkänd" in await page.locator("#course-map").inner_text()
   await page.locator("#year-select").select_option("2025")
   await page.locator('[data-family="trail43"]').click()
   runner=next(r for r in data["data/races/2025-trail43.json"]["results"] if r.get("name") and r["status"]=="FINISHED")
   await page.locator("#runner-search").fill(runner["name"].split()[0])
   assert await page.locator(".suggestion").count()>0
   await page.locator(".suggestion").first.click()
   assert await page.locator("#profile-dialog").evaluate("e=>e.open")
   assert await page.locator(".insight").count()>0
   await page.locator('[data-close="profile-dialog"]').click()
   await page.locator('#goal-placement-time').fill('10:00:00')
   await page.locator('#goal-placement-run').click()
   assert 'placering' in (await page.locator('#goal-placement').inner_text()).lower()
   await page.locator('#target-time').fill('10:00:00')
   await page.locator('#calculate-plan').click()
   assert await page.locator('#plan-table tbody tr').count()>0
   assert '10:00:00' in await page.locator('#plan-table tbody tr').last.inner_text()
   classes=Counter(r['class_name'] for r in data['data/races/2025-trail43.json']['results'] if r['status']=='FINISHED' and r.get('class_name'))
   await page.locator('#plan-cohort').select_option('class')
   await page.locator('#plan-class').select_option(classes.most_common(1)[0][0])
   assert 'klassen' in await page.locator('#plan-summary').inner_text()
   assert '10:00:00' in await page.locator('#plan-table tbody tr').last.inner_text()
   await page.locator('[data-plan-segment]').first.click()
   assert 'Illustrativ position' in await page.locator('#course-scrub-label').inner_text()
   await page.locator('#plan-cohort').select_option('all')
   await page.locator('#sex-filter').select_option('F')
   await page.locator('#sex-filter').select_option('all')
   await page.wait_for_timeout(120)
   overflow=await page.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
   assert overflow<=1,(width,overflow)
   assert not errors,(width,errors)
   assert not await page.evaluate("window.__missing||[]"),(width,"missing data")
   await page.screenshot(path=str(OUT/("satila-"+str(width)+".png")),full_page=True)
   print("PASS browser",width,height,"overflow",overflow,flush=True)
   await page.close()
  await browser.close()
 print("PASS 27 real editions and 3272 result appearances",flush=True)
asyncio.run(main())
