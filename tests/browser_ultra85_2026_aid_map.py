#!/usr/bin/env python3
"""Real-browser acceptance for public 2026 ultra aid map and personal replay.

Does not print participant identity or copy private FIT. Uses published data only.
"""
import asyncio,json,os,re
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path(os.environ.get("SATILA_SITE","docs"))

def fixtures():
    boot=json.loads((ROOT/"data/bootstrap.json").read_text(encoding="utf-8"))
    data={"data/bootstrap.json":boot}
    for ed in boot["editions"]:
        file=ROOT/"data/races"/(ed["race_key"]+".json")
        data["data/races/"+file.name]=json.loads(file.read_text(encoding="utf-8"))
    for file in (ROOT/"data/routes").glob("*.json"):
        data["data/routes/"+file.name]=json.loads(file.read_text(encoding="utf-8"))
    for file in (ROOT/"data").glob("*.json"):
        data["data/"+file.name]=json.loads(file.read_text(encoding="utf-8"))
    return data

async def main():
    data=fixtures()
    source=(ROOT/"index.html").read_text(encoding="utf-8")
    source=re.sub(r"<link [^>]*>","",source)
    source=re.sub(r"<script[^>]*>\s*</script>","",source)
    race=data["data/races/2026-ultra85.json"]
    runner=next(r for r in race["results"] if r["status"]=="FINISHED" and
                sum(x["result_id"]==r["id"] for x in race["splits"])>=2)
    async with async_playwright() as pw:
        opts={"headless":True}
        if Path("/usr/bin/chromium").exists():
            opts.update(executable_path="/usr/bin/chromium",args=["--no-sandbox"])
        browser=await pw.chromium.launch(**opts)
        try:
            for w,h in ((390,844),(1440,900)):
                page=await browser.new_page(viewport={"width":w,"height":h})
                errors=[]
                page.on("pageerror",lambda exc:errors.append(type(exc).__name__))
                await page.set_content(source)
                await page.add_style_tag(content=(ROOT/"assets/style.css").read_text(encoding="utf-8"))
                extra=ROOT/"assets/style-extra.css"
                if extra.exists():
                    await page.add_style_tag(content=extra.read_text(encoding="utf-8"))
                await page.evaluate("""data=>{
                  window.__fixtures=data;
                  window.fetch=async input=>{
                    const url=String(input);
                    const val=window.__fixtures[url];
                    return {ok:val!==undefined,status:val===undefined?404:200,json:async()=>val};
                  };
                }""",data)
                await page.add_script_tag(content=(ROOT/"assets/profile-analysis.js").read_text(encoding="utf-8"))
                await page.add_script_tag(content=(ROOT/"assets/app.js").read_text(encoding="utf-8"))
                await page.locator('[data-family="ultra85"]').click()
                await page.locator("#year-select").select_option("2026")
                await page.wait_for_function("document.querySelector('#race-title').textContent.includes('85 km · 2026')")
                aids=page.locator("#course-map [data-aid]")
                assert await aids.count()==6,(w,"aid pins")
                elev=page.locator("#course-elevation [data-aid-elevation]")
                assert await elev.count()==6,(w,"elevation aid pins")
                for name,km in [("Navåsen",22.7),("Helsjön",37.8),("Äskhult",54.6),
                                 ("Fjärås",63.4),("Lerbäck",72.8),("Ramhultafallet",81.4)]:
                    node=page.locator('#course-map [data-aid="'+name+'"]')
                    assert await node.count()==1,(w,"missing depot",name)
                    assert km>0
                    assert await page.locator('#course-elevation [data-aid-elevation="'+name+'"]').count()==1
                await page.locator("#runner-search").fill(runner["name"])
                await page.locator("#runner-suggestions .suggestion").first.click()
                dialog=page.locator("#profile-dialog")
                await dialog.wait_for(state="visible")
                assert await dialog.locator("#profile-mini-map [data-aid]").count()==6
                assert await dialog.locator("#profile-mini-elev [data-aid-elevation]").count()==6
                scrub=page.locator("#profile-replay-range")
                await scrub.evaluate("""el=>{el.value='35.6';el.dispatchEvent(new Event('input',{bubbles:true}))}""")
                await page.wait_for_function("""()=>
                  document.querySelector('[data-profile-live="segment"]')?.textContent
                    .includes('Navåsen → Helsjön')""")
                assert abs(float(await scrub.input_value())-35.6)<.12
                assert not errors,(w,"JavaScript errors",errors)
                await page.close()
            print("PASS 2026 ultra six official aid positions and 35.6 km Navåsen-Helsjön replay, mobile+desktop",flush=True)
        finally:
            await browser.close()

if __name__=="__main__":
    asyncio.run(main())
