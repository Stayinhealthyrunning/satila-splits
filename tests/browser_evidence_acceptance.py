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
    # Codex's coverage dashboard loads an additional valid public root JSON.
    # Load ALL committed root manifests rather than hiding missing fetches.
    for manifest in (ROOT/"data").glob("*.json"):
        fixtures["data/"+manifest.name]=json.loads(manifest.read_text(encoding="utf-8"))
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
            # The acceptance must exercise REAL responsive styles; an unstyled
            # long table makes a false-positive 390px overflow regression.
            await page.add_style_tag(content=(ROOT/"assets/style.css").read_text(encoding="utf-8"))
            extra=ROOT/"assets/style-extra.css"
            if extra.exists():
                await page.add_style_tag(content=extra.read_text(encoding="utf-8"))
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
            # All published DNF records currently lack a linked public TIME passage.
            # A numeric zero in the segment-exit column would incorrectly imply
            # that actual last checkpoints are known and none exited here.
            dnf_cells=await seg.locator("td:nth-child(9)").all_text_contents()
            assert len(dnf_cells)==7 and all(value.strip()=="Okänt" for value in dnf_cells),dnf_cells
            assert "inte noll avbrott" in await page.locator("#segments").inner_text()
            # D22 Course Intelligence must follow the SAME selected real segment
            # as the timing table, without inventing a DNF exit or segment ascent.
            intel=page.locator("#course-intelligence")
            await page.wait_for_function("document.querySelector('#course-intelligence')?.textContent.includes('Vald delsträcka:')")
            assert "Okänt" in await intel.inner_text()
            assert "Segmentets D+/D−" in await intel.inner_text()
            chosen=await seg.nth(1).locator("td").first.inner_text()
            await seg.nth(1).click()
            await page.wait_for_function("(label) => document.querySelector('#course-intelligence')?.textContent.includes('Vald delsträcka: '+label)",arg=chosen)
            # D11: real last-segment strength is separate from last-third placing.
            await page.wait_for_function("document.querySelector('#finish-progression')?.textContent.includes('Styrka på sista verifierade delsträckan')")
            assert "fältmedian" in await page.locator("#finish-progression").inner_text()
            # D07/D21: public class in scatter tooltip and honest changing checkpoint n.
            scatter_titles=await page.locator('#placement-chart circle title').all_text_contents()
            assert scatter_titles and all((' · Man · ' in t or ' · Kvinna · ' in t) for t in scatter_titles),scatter_titles[:3]
            await page.wait_for_function("document.querySelector('#checkpoint-spread')?.textContent.includes('Varje kontroll använder sitt eget observerade n')")
            # D18/D19 use identical user-selected class groups, not separate top-N lists.
            await page.wait_for_function("document.querySelectorAll('#segment-groups [data-class-series]').length >= 2")
            checked=await page.locator('#segment-groups [data-class-series]:checked').evaluate_all("(els)=>els.map(e=>e.dataset.classSeries)")
            heat=await page.locator('#segment-heatmap .heat-label').all_text_contents()
            assert heat==checked,("Default class and heatmap selections diverged",heat,checked)
            await page.locator('#segment-groups [data-class-series]').first.evaluate("(el)=>el.click()")
            checked=await page.locator('#segment-groups [data-class-series]:checked').evaluate_all("(els)=>els.map(e=>e.dataset.classSeries)")
            heat=await page.locator('#segment-heatmap .heat-label').all_text_contents()
            assert len(checked)==1 and heat==checked,("Heatmap ignored changed user class selection",heat,checked)
            # T07: route publication and provenance reservation are explicitly separate.
            await page.wait_for_function("document.querySelector('#course-provenance')?.textContent.includes('Publik displayrutt')")
            assert "Verifieringsreservation" in await page.locator("#course-provenance").text_content()
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
