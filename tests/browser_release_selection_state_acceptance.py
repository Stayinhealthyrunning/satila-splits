#!/usr/bin/env python3
"""Edition-local UX state regression: goal default and selectable club/ort groups.

Only public curated results are used. Switching race/year must not silently
carry a prior race's default goal time or hide selected groups outside top ten.
"""
import asyncio,json,os,re,statistics
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path(os.getenv("SATILA_SITE","docs"))

def fixtures():
    root=json.loads((ROOT/"data/bootstrap.json").read_text(encoding="utf-8"))
    data={"data/bootstrap.json":root,"data/coverage.json":json.loads((ROOT/"data/coverage.json").read_text(encoding="utf-8"))}
    for ed in root["editions"]:
        file=ROOT/"data/races"/f"{ed['race_key']}.json"
        data["data/races/"+file.name]=json.loads(file.read_text(encoding="utf-8"))
    for file in (ROOT/"data/routes").glob("*.json"):
        data["data/routes/"+file.name]=json.loads(file.read_text(encoding="utf-8"))
    return data

async def assert_selection_consistent(page,where):
    await page.wait_for_selector("#club-chart .club-choices input[data-club-choice]")
    state=await page.evaluate("""()=>{
      const node=document.querySelector('#club-chart');
      const checked=[...node.querySelectorAll('.club-choices input[data-club-choice]:checked')].map(x=>x.dataset.clubChoice);
      const visible=[...node.querySelectorAll('.club-choices input[data-club-choice]')].map(x=>x.dataset.clubChoice);
      const selected=[...node.querySelectorAll('.club-choices + .table-scroll tbody tr')].map(tr=>tr.cells[0]?.textContent.trim());
      return {checked,visible,selected};
    }""")
    assert len(state["checked"])<=4,(where,state)
    assert len(state["checked"])==len(set(state["checked"])),(where,state)
    assert set(state["checked"])==set(state["selected"]),(where,state)
    assert set(state["selected"]).issubset(set(state["visible"])),(where,state)
    return state

def fmt_time(seconds):
    seconds=round(seconds);hours=seconds//3600;minutes=seconds%3600//60;secs=seconds%60
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"

async def assert_default_goal(page,data,race_key,where):
    finish=[r["finish_seconds"] for r in data[f"data/races/{race_key}.json"]["results"] if r["status"]=="FINISHED" and r.get("finish_seconds",0)>0]
    expected=fmt_time(statistics.mean(finish))
    await page.wait_for_function("expected=>document.querySelector('#goal-placement-time')?.value===expected",arg=expected,timeout=10000)
    val=await page.locator("#goal-placement-time").input_value()
    assert val==expected,(where,val,expected)
    assert await page.locator("#goal-placement-time").get_attribute("data-default-source")=="finished-mean"
    return val

async def main():
    data=fixtures()
    source=(ROOT/"index.html").read_text(encoding="utf-8")
    source=re.sub(r"<link [^>]*>","",source)
    source=re.sub(r"<script[^>]*>\s*</script>","",source)
    script=(ROOT/"assets/app.js").read_text(encoding="utf-8")
    async with async_playwright() as pw:
        options={"headless":True}
        if Path("/usr/bin/chromium").exists():options.update(executable_path="/usr/bin/chromium",args=["--no-sandbox"])
        browser=await pw.chromium.launch(**options)
        try:
            for width,height in ((1440,900),(390,844)):
                page=await browser.new_page(viewport={"width":width,"height":height})
                page.set_default_timeout(8000)
                errors=[];page.on("pageerror",lambda e:errors.append(str(e)))
                await page.set_content(source)
                await page.add_style_tag(content=(ROOT/"assets/style.css").read_text(encoding="utf-8"))
                await page.add_style_tag(content=(ROOT/"assets/style-extra.css").read_text(encoding="utf-8"))
                await page.evaluate("""d=>{
                   window.__fixtures=d;window.__missing=[];
                   window.fetch=async u=>{
                     const v=window.__fixtures[String(u)];
                     if(v===undefined)window.__missing.push(String(u));
                     return {ok:v!==undefined,status:v===undefined?404:200,json:async()=>v};
                   };
                }""",data)
                await page.add_script_tag(content=script)
                await page.wait_for_function("document.querySelector('#race-title')?.textContent.includes('43 km · 2025')")
                original=await assert_default_goal(page,data,"2025-trail43",(width,"trail43-default"))
                await assert_selection_consistent(page,(width,"trail43-default"))
                await page.locator("#goal-placement-time").fill("15:55:44")
                await page.locator('[data-family="ultra85"]').click()
                await page.wait_for_function("document.querySelector('#race-title')?.textContent.includes('85 km · 2025')")
                changed=await assert_default_goal(page,data,"2025-ultra85",(width,"ultra85"))
                assert original!=changed,(width,original,changed)
                await page.locator('[data-family="trail43"]').click()
                await page.wait_for_function("document.querySelector('#race-title')?.textContent.includes('43 km · 2025')")
                await assert_default_goal(page,data,"2025-trail43",(width,"trail43-return"))
                selection=await assert_selection_consistent(page,(width,"trail43"))
                assert len(selection["checked"])==3,(width,selection)
                first_unchecked=page.locator("#club-chart input[data-club-choice]:not(:checked):not(:disabled)").first
                new_club=await first_unchecked.get_attribute("data-club-choice")
                # The UI immediately recreates its checkbox subtree. click() is
                # appropriate; check() would wait on the detached old element.
                await first_unchecked.click()
                await page.wait_for_function("""name=>[...document.querySelectorAll('#club-chart input[data-club-choice]:checked')]
                   .some(input=>input.dataset.clubChoice===name)""",arg=new_club)
                selection=await assert_selection_consistent(page,(width,"trail43-added"))
                assert len(selection["checked"])==4,(width,selection)
                await page.locator("#sex-filter").select_option("F")
                await assert_selection_consistent(page,(width,"female-filter"))
                await page.locator("#sex-filter").select_option("all")
                await assert_selection_consistent(page,(width,"unfiltered"))
                await page.locator("#goal-placement-time").fill("14:10:05")
                await page.locator("#year-select").select_option("2024")
                await page.wait_for_function("document.querySelector('#race-title')?.textContent.includes('43 km · 2024')")
                await assert_default_goal(page,data,"2024-trail43",(width,"2024"))
                selection=await assert_selection_consistent(page,(width,"year-changed"))
                assert len(selection["checked"])==3,(width,selection)
                assert not errors,(width,errors)
                assert not await page.evaluate("window.__missing||[]"),width
                print("PASS edition-local goal defaults + visible club selection:",width,height,flush=True)
                await page.close()
        finally:await browser.close()

if __name__=="__main__":asyncio.run(main())
