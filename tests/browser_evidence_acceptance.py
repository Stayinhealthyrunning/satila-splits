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
            assert count==6,("2025 43 km: expected six REAL analysis segments after removal of the nonofficial early station",count)
            names=await seg.all_text_contents()
            assert any("Start" in s and "Torrås" in s for s in names)
            assert all("Grind" not in s for s in names)
            assert all("Tostared" not in s for s in names)
            # The redundant passage-coverage card is deliberately removed. The
            # source rule still applies in the timing table: metadata-only
            # Tostared must not create a false observed segment.
            assert await page.locator('#segment-retention').count()==0
            # The compact segment table intentionally keeps only the six requested analytical columns.
            headers=[x.strip() for x in await page.locator("#segment-table th").all_text_contents()]
            assert headers==["Delsträcka","km*","n","Median","Q25–Q75","Tempo"],headers
            assert "Parvis täckning" not in await page.locator("#segments").inner_text()
            # D22 Course Intelligence must follow the SAME selected real segment
            # as the timing table, without inventing a DNF exit or segment ascent.
            intel=page.locator("#course-intelligence")
            await page.wait_for_function("document.querySelector('#course-intelligence')?.textContent.includes('Vald delsträcka:')")
            assert "Okänt" in await intel.inner_text()
            assert "Segmentets D+/D−" in await intel.inner_text()
            chosen=await seg.nth(1).locator("td").first.inner_text()
            await seg.nth(1).click()
            await page.wait_for_function("(label) => document.querySelector('#course-intelligence')?.textContent.includes('Vald delsträcka: '+label)",arg=chosen)
            # K03: D14, D15, D17, D18 and D19 all share the same selected
            # real timing segment, podium selector, table, Course Intelligence
            # and official-route display overlay (never athlete GPS).
            await page.locator('#podium-segment-start').select_option('2')
            await page.wait_for_function("document.querySelector('#segment-chart [data-segment=\"2\"]')?.getAttribute('r')==='7'")
            assert 'selected' in (await seg.nth(2).get_attribute('class') or '')
            await page.locator('#segment-chart [data-segment="1"]').click()
            assert await page.locator('#podium-segment-start').input_value()=='1'
            await page.locator('#segment-sex-extra [data-extra-segment="3"]').first.focus()
            await page.keyboard.press('Enter')
            await page.wait_for_function("document.querySelector('#podium-segment-start')?.value==='3'")
            await page.wait_for_function("Array.from(document.querySelectorAll('#segment-sex-extra [data-extra-segment]')).some(el=>el.dataset.extraSegment==='3'&&el.getAttribute('aria-pressed')==='true')")
            assert 'selected' in (await seg.nth(3).get_attribute('class') or '')
            assert await page.locator('#segment-chart [data-segment="3"]').get_attribute('r')=='7'
            assert await page.locator('#segment-sex-extra [data-extra-segment="3"]').first.get_attribute('aria-pressed')=='true'
            spread_labels=page.locator('#checkpoint-spread .checkpoint-axis-label')
            assert await spread_labels.count()==6
            boxes=[await spread_labels.nth(i).bounding_box() for i in range(await spread_labels.count())]
            assert all(boxes[i]['x']+boxes[i]['width']<=boxes[i+1]['x']+1 for i in range(len(boxes)-1)),boxes
            segment_name=await seg.nth(3).locator('td').first.inner_text()
            assert 'Vald delsträcka: '+segment_name in await intel.inner_text()
            assert await page.locator('#course-map .segment-route-overlay').count()==1
            # Segment selection seeks map AND elevation to the same approximate
            # display-route midpoint; it must never invent a precise station GPS.
            map_d=float(await page.locator('#course-map [data-map-hit]').get_attribute('aria-valuenow'))
            elev_d=float(await page.locator('#course-elevation [data-elev-hit]').get_attribute('aria-valuenow'))
            assert map_d>0 and abs(map_d-elev_d)<.001,(map_d,elev_d)
            assert 'proportionellt uppskattad' in await page.locator('#course-scrub-label').inner_text()
            assert 'ingen verifierad kontrollprojektion' in await page.locator('#course-map .segment-route-overlay').get_attribute('aria-label')
            await page.locator('#segment-sex-extra [data-extra-segment="4"]').first.click()
            await page.wait_for_function("document.querySelector('#podium-segment-start')?.value==='4'")
            await page.locator('#segment-sex-extra [data-extra-segment="5"]').first.focus()
            await page.keyboard.press(' ')
            await page.wait_for_function("document.querySelector('#podium-segment-start')?.value==='5'")
            assert await page.locator('#segment-heatmap').count()==0
            # D11: real last-segment strength is separate from last-third placing.
            await page.wait_for_function("document.querySelector('#finish-progression')?.textContent.includes('Snabbaste avslutningen')")
            assert "Spurten mot mål" in await page.locator("#extra-dynamics").inner_text()
            assert "100 = median" in await page.locator("#last-segment-strength").inner_text()
            # D07/D21: public class in scatter tooltip and honest changing checkpoint n.
            scatter_titles=await page.locator('#placement-chart circle title').all_text_contents()
            assert scatter_titles and all((' · Man · ' in t or ' · Kvinna · ' in t) for t in scatter_titles),scatter_titles[:3]
            # D07: percentile-based chart zoom reduces visible runners and reset restores
            # the exact initial count on both desktop and mobile.
            scatter=page.locator("#placement-chart")
            count_full=await scatter.locator("circle[data-open]").count()
            assert count_full>8,("D07 insufficient fixture field for zoom",count_full)
            await scatter.locator("#placement-zoom-in").click()
            assert "P10–P90" in await scatter.locator('[role="status"]').inner_text()
            count_first=await scatter.locator("circle[data-open]").count()
            assert 1<count_first<count_full,("D07 first zoom",count_first,count_full)
            await scatter.locator("#placement-zoom-in").click()
            assert "P25–P75" in await scatter.locator('[role="status"]').inner_text()
            count_second=await scatter.locator("circle[data-open]").count()
            assert 1<count_second<count_first,("D07 second zoom",count_second,count_first)
            assert await scatter.locator("#placement-zoom-in").is_disabled()
            await scatter.locator("#placement-zoom-reset").click()
            assert await scatter.locator("circle[data-open]").count()==count_full
            assert "Hela fältet" in await scatter.locator('[role="status"]').inner_text()
            await page.wait_for_function("document.querySelector('#checkpoint-spread')?.textContent.includes('Varje kontroll använder sitt eget observerade n')")
            # D18 uses one explicit, capped class selector rather than a second
            # opaque comparison or heatmap.
            await page.wait_for_function("document.querySelectorAll('#segment-groups [data-class-series]').length >= 2")
            checked=await page.locator('#segment-groups [data-class-series]:checked').evaluate_all("(els)=>els.map(e=>e.dataset.classSeries)")
            assert 1<=len(checked)<=5,checked
            await page.locator('#segment-groups [data-class-series]').first.evaluate("(el)=>el.click()")
            checked=await page.locator('#segment-groups [data-class-series]:checked').evaluate_all("(els)=>els.map(e=>e.dataset.classSeries)")
            assert len(checked)>=1,checked
            # T01: all varying source fields are selectable, and the native
            # control responds to keyboard interaction on desktop and mobile.
            sort=page.locator('#results-sort')
            assert await sort.locator('option').count()==11
            await sort.focus()
            await sort.press('End')
            assert await sort.input_value()=='status'
            statuses=await page.locator('#results-table tbody tr td:nth-child(9)').all_text_contents()
            assert statuses and all(v.strip()=='FINISHED' for v in statuses),statuses[:5]
            await sort.select_option('time_desc')
            shown=await page.locator('#results-table tbody tr td:nth-child(10)').all_text_contents()
            def time_in_seconds(v):
                parts=[int(x) for x in v.strip().split(':')]
                return sum(x*(60**i) for i,x in enumerate(reversed(parts)))
            seconds=[time_in_seconds(v) for v in shown if ':' in v]
            assert len(seconds)>=5 and seconds==sorted(seconds,reverse=True),seconds[:8]
            await sort.select_option('club')
            club_cells=await page.locator('#results-table tbody tr td:nth-child(8)').all_text_contents()
            assert club_cells and all(v.strip() for v in club_cells),"Missing clubs must sort after populated sources"
            await sort.select_option('place')
            # T07: route publication and provenance reservation are explicitly separate.
            await page.wait_for_function("document.querySelector('#course-provenance')?.textContent.includes('Publik displayrutt')")
            assert "Verifieringsreservation" in await page.locator("#course-provenance").text_content()
            # A target plan should reflect all six accepted analytical segments.
            await page.locator("#target-time").fill("10:00:00")
            await page.locator("#calculate-plan").click()
            plan=page.locator("#plan-table tbody tr")
            assert await plan.count()==6,"2025/43: exactly six accepted effective sections"
            methods=await plan.locator("td:nth-child(4)").all_text_contents()
            assert len(methods)==6 and all("Historisk" in s for s in methods),methods
            summary=await page.locator("#plan-summary").inner_text()
            assert "6/6" in summary,summary
            # The native hidden property of the optional reference-class
            # label must survive the responsive author CSS display rules.
            optional_class=page.locator("#plan-class-label")
            assert await page.locator("#plan-cohort").input_value()=="all"
            assert await optional_class.is_hidden(),"Reference class shown in whole-field mode"
            await page.locator("#plan-cohort").select_option("class")
            assert await optional_class.is_visible(),"Class selector missing in class cohort mode"
            await page.locator("#plan-cohort").select_option("all")
            assert await optional_class.is_hidden(),"Reference class remained visible after reset"
            # T06: expose source confidence rather than fabricating segment D+/D-.
            plan_head=await page.locator('#plan-table thead th').all_text_contents()
            assert plan_head[-2:]==['D+/D−*','Underlag'],plan_head
            elevation=await plan.locator('td:nth-child(8)').all_text_contents()
            assert len(elevation)==6 and all(x.strip()=='Ej verifierat' for x in elevation),elevation
            sources=await plan.locator('td:nth-child(9)').all_text_contents()
            assert len(sources)==6 and all('EQ Timing TIME-par' in x and 'observerad tidsandel' in x for x in sources),sources
            assert 'Ingen höjd per timingsegment' in await page.locator('#plan-table').locator('xpath=../following-sibling::p').inner_text()
            if w<=700:
                assert 'Svep i sidled' in await page.locator('#plan-summary + p.mobile-table-hint').inner_text()
            assert await page.locator('#segment-q1090').count()==0
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
