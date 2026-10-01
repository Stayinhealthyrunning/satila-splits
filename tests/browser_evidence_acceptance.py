#!/usr/bin/env python3
"""Codex acceptance: inspect real browser UI for three known source edge cases.

This deliberately does NOT run in the source-audit CI yet: the previous
first draft still renders metadata-only Tostared as a 0-observation boundary.
Enable this E2E acceptance test in the frontend CI once Codex implements the
effective source-observed station axis. No network request to live EQ Timing.
"""
from __future__ import annotations
import asyncio,json,re,os
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path(os.getenv("SATILA_SITE",Path(__file__).resolve().parents[1]/"docs"))

async def main():
    boot=json.loads((ROOT/"data/bootstrap.json").read_text(encoding="utf-8"))
    fixtures={"data/bootstrap.json":boot}
    for e in boot["editions"]:
        path=ROOT/"data/races"/(e["race_key"]+".json")
        fixtures["data/races/"+path.name]=json.loads(path.read_text(encoding="utf-8"))
    for p in (ROOT/"data/routes").glob("*.json"):
        fixtures["data/routes/"+p.name]=json.loads(p.read_text(encoding="utf-8"))
    markup=(ROOT/"index.html").read_text(encoding="utf-8")
    markup=re.sub(r"<link [^>]*>","",markup)
    markup=re.sub(r"<script[^>]*>\s*</script>","",markup)
    js=(ROOT/"assets/app.js").read_text(encoding="utf-8")
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        for w,h in ((1440,900),(390,844)):
            page=await browser.new_page(viewport={"width":w,"height":h})
            errors=[]
            page.on("pageerror",lambda e:errors.append(str(e)))
            await page.set_content(markup)
            await page.evaluate("""data=>{
              window.__fixtures=data;
              window.fetch=async url=>{
                const datum=window.__fixtures[String(url)];
                return {ok:datum!==undefined,status:datum===undefined?404:200,json:async()=>datum};
              };
            }""",fixtures)
            await page.add_script_tag(content=js)
            await page.wait_for_function("document.querySelector('#race-title').textContent.includes('2025')")
            # Case 1: metadata-only Tostared must not create two artificial 0-data segments.
            await page.locator('[data-family="trail43"]').click()
            await page.wait_for_function("document.querySelector('#race-title').textContent.includes('43 km')")
            seg=page.locator("#segment-table tbody tr")
            count=await seg.count()
            assert count==7,("2025 43 km: expected seven REAL combined analysis segments, not eight metadata segments",count)
            names=await seg.all_text_contents()
            assert any("Grind" in s and "Torrås" in s for s in names)
            assert all("Tostared" not in s for s in names)
            # A target plan should reflect all seven real measured segments.
            await page.locator("#target-time").fill("10:00:00")
            await page.locator("#calculate-plan").click()
            plan=page.locator("#plan-table tbody tr")
            assert await plan.count()==7,"2025/43: a source-only pacing plan has exactly seven effective sections"
            methods=await plan.locator("td:nth-child(4)").all_text_contents()
            assert len(methods)==7 and all("Historisk" in s for s in methods),methods
            summary=await page.locator("#plan-summary").inner_text()
            assert "7/7" in summary,summary
            # Case 2: two sparsely observed 2023 43-km segments do not get invented quartiles.
            await page.locator("#year-select").select_option("2023")
            await page.wait_for_function("document.querySelector('#race-title').textContent.includes('2023')")
            found=0
            for row in await page.locator("#segment-table tbody tr").all():
                cells=await row.locator("td").all_text_contents()
                if any(a in cells[0] and b in cells[0] for a,b in (("Almered","Skolan"),("Skolan","Ramhulta"))):
                    found+=1
                    assert int(cells[2].strip())==8,cells
                    assert "n < 10" in cells[4],cells
            assert found==2,("2023 43 km sparse segments not displayed",found)
            # Case 3: 2016 85-km official source has two women finishers, not three.
            await page.locator('[data-family="ultra85"]').click()
            await page.locator("#year-select").select_option("2016")
            await page.wait_for_function("document.querySelector('#race-title').textContent.includes('2016')")
            podium=page.locator("#overall-podium .podium-group")
            assert await podium.count()==2
            assert await podium.nth(0).locator(".podium-row").count()==2
            assert await podium.nth(1).locator(".podium-row").count()==3
            assert not errors,(w,errors)
            overflow=await page.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
            assert overflow<=1,(w,overflow)
            print("ACCEPTANCE PASS",w,h,": 2025 station bridge, 2023 low-n, 2016 women podium",flush=True)
            await page.close()
        await browser.close()

if __name__=="__main__":
    asyncio.run(main())
