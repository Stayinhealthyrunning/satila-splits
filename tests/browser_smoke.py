#!/usr/bin/env python3
"""Offline Chromium regression: committed Sätila results, no live EQ requests."""
import asyncio,base64,json,os,re
from collections import Counter
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(os.getenv("SATILA_SITE","docs"))
OUT=Path(os.getenv("SATILA_QA_OUTPUT","/tmp/satila-qa"))
OUT.mkdir(parents=True,exist_ok=True)
async def assert_full_osm(page,host):
 """Every displayed OSM map must cover the viewBox, without grey letterboxing."""
 result=await page.locator(host).evaluate("""node=>{
   const svg=node.querySelector('svg'),layer=svg?.querySelector('.osm-tile-layer'),
     images=Array.from(layer?.querySelectorAll('image')||[]);
   if(!svg||!images.length)return {full:false,tileCount:0};
   const view=svg.viewBox.baseVal;
   const minX=Math.min(...images.map(img=>img.x.baseVal.value)),
     minY=Math.min(...images.map(img=>img.y.baseVal.value)),
     maxX=Math.max(...images.map(img=>img.x.baseVal.value+img.width.baseVal.value)),
     maxY=Math.max(...images.map(img=>img.y.baseVal.value+img.height.baseVal.value));
   return {full:minX<=view.x+1&&minY<=view.y+1&&
     maxX>=view.x+view.width-1&&maxY>=view.y+view.height-1,
     tileCount:images.length,zoom:Number(layer.dataset.zoom)};
 }""")
 assert result["full"],(host,"OSM must fill SVG map viewport",result)
 assert 1<=result["tileCount"]<=24,(host,"OSM tile budget",result)
 assert 8<=result["zoom"]<=15,(host,"OSM adaptive zoom",result)

async def main():
 b=json.loads((ROOT/"data/bootstrap.json").read_text(encoding="utf-8"))
 assert len(b["editions"])==27 and sum(e["results"] for e in b["editions"])==3272
 data={"data/bootstrap.json":b,"data/coverage.json":json.loads((ROOT/"data/coverage.json").read_text(encoding="utf-8"))}
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
 hero=base64.b64encode((ROOT/"assets/hero.webp").read_bytes()).decode("ascii")
 css=css.replace("url('hero.webp')","url('data:image/webp;base64,"+hero+"')")
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
   assert "43 km" in await page.locator("#race-title").inner_text()
   assert await page.locator("#segment-table tbody tr").count()>0
   assert 'Fullföljandegrad:' in await page.locator('.kpi-note').inner_text()
   assert await page.locator('#results-table th').count()==11
   assert await page.locator('#segment-table th').count()==10
   for ex in ("#extra-overview","#extra-dynamics","#extra-segments","#extra-course","#extra-history","#segment-heatmap","#history-fingerprint","#coverage-table"):
    assert await page.locator(ex).count()==1,(width,ex)
   try:
    await page.wait_for_selector('#coverage-table table',timeout=5000)
   except Exception:
    print('COVERAGE_DIAGNOSTICS',width,await page.locator('#coverage-table').inner_text(),errors,await page.evaluate('window.__missing||[]'),flush=True)
    raise
   assert await page.locator('#coverage-table th').count()>=10
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
   assert await page.locator('#course-map .osm-tile-layer image').count()>0
   assert await page.locator('#course-map .osm-attribution').count()==1
   await assert_full_osm(page,'#course-map')
   assert await page.locator('#finish-series [data-finish-mode]').count()==3
   await page.locator('#finish-series [data-finish-mode="F"]').click()
   assert await page.locator('#finish-series [data-finish-mode="F"]').get_attribute('aria-pressed')=='true'
   await page.locator('#finish-series [data-finish-mode="all"]').click()
   assert await page.locator('#finish-series [data-finish-mode="all"]').get_attribute('aria-pressed')=='true'
   assert await page.locator('#group-table th').count()==5
   assert await page.locator('#group-table #group-next').count()==1
   await page.locator('#group-table #group-next').click()
   assert 'Sida 2' in await page.locator('#group-table .pagination').inner_text()
   await page.locator('#group-table #group-prev').click()
   assert await page.locator('#segment-pacing circle[data-pacing-segment]').count()>0
   assert await page.locator('#percentile-chart svg').count()==1
   assert await page.locator('#segment-sex-extra svg').count()==1
   assert await page.locator('#segment-groups svg').count()==1
   assert await page.locator('[data-class-series]:checked').count()<=5
   assert await page.locator('#segment-heatmap .heat-cell small').count()>0
   assert await page.locator('#history-table th').count()==15
   assert await page.locator('#club-chart .club-choice').count()>0
   await page.wait_for_selector('#course-provenance table')
   assert 'SHA-256' in await page.locator('#course-provenance').inner_text()
   runner=next(r for r in data["data/races/2025-trail43.json"]["results"] if r.get("name") and r["status"]=="FINISHED")
   await page.locator("#runner-search").fill(runner["name"].split()[0])
   assert await page.locator(".suggestion").count()>0
   await page.locator(".suggestion").first.click()
   assert await page.locator("#profile-dialog").evaluate("e=>e.open")
   assert await page.locator(".insight").count()>0
   assert any('Sedan föregående verifierade' in value for value in await page.locator('#profile-content th').all_text_contents())
   assert await page.locator('#profile-content .insight small').count()>0
   assert await page.locator('#profile-replay-duration option').count()==4
   assert await page.locator('#profile-mini-map .osm-tile-layer image').count()>0
   assert await page.locator('#profile-mini-map .osm-attribution').count()==1
   await assert_full_osm(page,'#profile-mini-map')
   await page.locator('#profile-replay-play').click()
   await page.wait_for_timeout(550)
   assert float(await page.locator('#profile-replay-range').input_value())>0
   await page.locator('#profile-replay-play').click()
   replay_position=await page.locator('#profile-replay-range').input_value()
   await page.locator('#profile-replay-follow').click()
   assert await page.locator('#profile-replay-follow').get_attribute('aria-pressed')=='true'
   await page.locator('#profile-replay-fit').click()
   assert await page.locator('#profile-replay-follow').get_attribute('aria-pressed')=='false'
   assert await page.locator('#profile-replay-range').input_value()==replay_position
   await page.locator('#profile-replay-reset').click()
   assert float(await page.locator('#profile-replay-range').input_value())==0
   await page.locator('#profile-add-duel').click()
   await page.locator('#profile-add-compare').click()
   await page.locator('[data-close="profile-dialog"]').click()
   second=next(r for r in data['data/races/2025-trail43.json']['results'] if r['status']=='FINISHED' and r['id']!=runner['id'] and r.get('name'))
   await page.locator('#results-search').fill(second['name'])
   await page.locator('#results-table [data-open="'+second['id']+'"]').first.click()
   await page.locator('#profile-add-duel').click()
   await page.locator('#profile-add-compare').click()
   await page.locator('[data-close="profile-dialog"]').click()
   await page.locator('#open-compare').click()
   assert await page.locator('#compare-dialog').evaluate('e=>e.open')
   assert any('A segment' in value for value in await page.locator('#compare-dialog th').all_text_contents())
   assert await page.locator('#duel-map svg').count()==1
   assert await page.locator('#duel-map .osm-tile-layer image').count()>0
   assert await page.locator('#duel-map .osm-attribution').count()==1
   await assert_full_osm(page,'#duel-map')
   await page.locator('#duel-zoom').fill('2')
   zoomed=await page.locator('#duel-map svg').get_attribute('viewBox')
   assert float(zoomed.split()[2])<760
   await page.locator('#duel-fit').click()
   assert float((await page.locator('#duel-map svg').get_attribute('viewBox')).split()[2])==760
   await page.locator('#duel-elevation svg').click(position={'x':120,'y':60})
   assert float(await page.locator('#duel-range').input_value())>0
   await page.locator('[data-close="compare-dialog"]').click()
   await page.locator('#results-search').fill('')
   await page.locator('#open-map-duel').click()
   assert await page.locator('#map-duel-dialog').evaluate('e=>e.open')
   assert await page.locator('#map-duel-map [data-runner-marker]').count()==2
   assert await page.locator('#map-duel-map .osm-tile-layer image').count()>0
   assert await page.locator('#map-duel-map .osm-attribution').count()==1
   await assert_full_osm(page,'#map-duel-map')
   assert await page.locator('#map-duel-leaderboard tbody tr').count()==2
   await page.locator('#map-duel-camera').select_option('leader')
   assert float((await page.locator('#map-duel-map svg').get_attribute('viewBox')).split()[2])<760
   await page.locator('#map-duel-fit').click()
   assert float((await page.locator('#map-duel-map svg').get_attribute('viewBox')).split()[2])==760
   await page.locator('#map-duel-play').click()
   await page.wait_for_timeout(250)
   await page.locator('#map-duel-play').click()
   assert float(await page.locator('#map-duel-clock').input_value())>0
   await page.locator('#map-duel-reset').click()
   assert float(await page.locator('#map-duel-clock').input_value())==0
   map_duel=page.locator('#map-duel-dialog')
   assert await map_duel.evaluate("(d)=>d.scrollWidth<=d.clientWidth+1"),(
    width,"map duel dialog has horizontal overflow")
   await map_duel.screenshot(path=str(OUT/("map-duel-"+str(width)+".png")),animations="disabled")
   await page.locator('[data-close="map-duel-dialog"]').click()
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
   if width==390:
    no_overlap=await page.evaluate("()=>document.querySelector('.race-cards').getBoundingClientRect().bottom<=document.querySelector('#race-context .context-main').getBoundingClientRect().top")
    assert no_overlap,'Mobile race cards overlap the selected edition'
   overflow=await page.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
   assert overflow<=1,(width,overflow)
   assert not errors,(width,errors)
   assert not await page.evaluate("window.__missing||[]"),(width,"missing data")
   await page.locator('#results-search').fill('')
   await page.locator('#runner-search').fill('')
   await page.locator('#clear-compare').click()
   await page.locator('#clear-map-duel').click()
   await page.evaluate("document.querySelectorAll('.table-scroll,.chart-host').forEach(el=>el.scrollLeft=0)")
   assert await page.evaluate("Array.from(document.querySelectorAll('.table-scroll,.chart-host')).every(el=>el.scrollLeft===0)")
   await page.evaluate("window.scrollTo(0,0)")
   await page.wait_for_timeout(180)
   await page.screenshot(path=str(OUT/("satila-"+str(width)+".png")),full_page=True)
   print("PASS browser",width,height,"overflow",overflow,flush=True)
   await page.close()
  await browser.close()
 print("PASS 27 real editions and 3272 result appearances",flush=True)
asyncio.run(main())
