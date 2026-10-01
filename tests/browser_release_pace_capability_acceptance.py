#!/usr/bin/env python3
"""Release-only browser acceptance for pace-distance capability gating.

2023 trail43 has a known timing-km metadata anomaly at Torrås -> Almered.
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
            await page.locator("#year-select").select_option("2023")
            await page.wait_for_function("document.querySelector('#race-title').textContent.includes('43 km · 2023')")

            rows=page.locator("#segment-table tbody tr")
            target=None
            for i in range(await rows.count()):
                cells=await rows.nth(i).locator("td").all_text_contents()
                if cells and "Torrås" in cells[0] and "Almered" in cells[0]:
                    target=cells
                    break
            assert target is not None,"Known 2023 Torrås→Almered segment missing"
            # Median TIME must remain usable.
            assert target[3].strip() not in ("","—","-"),target
            # Pace must be unavailable OR explicitly qualified as unverified/time-only.
            pace=target[5].strip().lower() if len(target)>5 else ""
            qualified=(
                pace in ("","—","-","ej verifierad","saknas") or
                any(token in pace for token in ("tid-only","tid endast","distans ej verifierad","ej verifierad"))
            )
            assert qualified,(
                "Known questionable timing-km segment still exposes unqualified pace/min-km",
                target
            )
            print("RELEASE PACE-CAPABILITY ACCEPTANCE PASSED",target,flush=True)
        finally:
            await browser.close()

if __name__=="__main__":
    asyncio.run(main())
