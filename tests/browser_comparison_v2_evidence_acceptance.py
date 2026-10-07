#!/usr/bin/env python3
"""Real-data browser proof for Sätila-specific Comparison 2.0 fallbacks."""
from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path

from playwright.async_api import async_playwright


ROOT = Path(os.getenv("SATILA_SITE", "docs"))


def fixtures():
    boot = json.loads((ROOT / "data/bootstrap.json").read_text(encoding="utf-8"))
    data = {"data/bootstrap.json": boot}
    for edition in boot["editions"]:
        path = ROOT / "data/races" / f"{edition['race_key']}.json"
        data[f"data/races/{path.name}"] = json.loads(path.read_text(encoding="utf-8"))
    for path in (ROOT / "data/routes").glob("*.json"):
        data[f"data/routes/{path.name}"] = json.loads(path.read_text(encoding="utf-8"))
    for path in (ROOT / "data").glob("*.json"):
        data[f"data/{path.name}"] = json.loads(path.read_text(encoding="utf-8"))
    return data


async def select_two(page, race, runners=None):
    finishers = runners or sorted(
        (row for row in race["results"] if row["status"] == "FINISHED"),
        key=lambda row: row["finish_seconds"],
    )[:2]
    for runner in finishers:
        await page.locator("#runner-search").fill(runner["name"])
        await page.locator(f'#runner-suggestions [data-id="{runner["id"]}"]').click()
        await page.locator("#profile-add-compare").click()
        await page.locator('[data-close="profile-dialog"]').click()
    await page.locator("#open-compare").click()


async def main():
    data = fixtures()
    selected_case = os.getenv("SATILA_COMPARISON_CASE", "all")
    markup = re.sub(r"<link [^>]*>", "", (ROOT / "index.html").read_text(encoding="utf-8"))
    markup = re.sub(r"<script[^>]*>\s*</script>", "", markup)
    async with async_playwright() as playwright:
        options = {"headless": True}
        if Path("/usr/bin/chromium").exists():
            options.update(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        browser = await playwright.chromium.launch(**options)
        page = await browser.new_page(viewport={"width": 900, "height": 900})
        page.set_default_timeout(8000)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        await page.set_content(markup)
        await page.add_style_tag(content=(ROOT / "assets/style.css").read_text(encoding="utf-8"))
        await page.add_style_tag(content=(ROOT / "assets/style-extra.css").read_text(encoding="utf-8"))
        await page.evaluate(
            """payload=>{window.__fixtures=payload;window.fetch=async url=>{const value=window.__fixtures[String(url)];if(value===undefined)(window.__missing??=[]).push(String(url));return {ok:value!==undefined,status:value===undefined?404:200,json:async()=>value}}}""",
            data,
        )
        await page.add_script_tag(content=(ROOT / "assets/profile-analysis.js").read_text(encoding="utf-8"))
        await page.add_script_tag(content=(ROOT / "assets/app.js").read_text(encoding="utf-8"))
        await page.wait_for_function("document.querySelector('#race-title').textContent.includes('2025')")

        if selected_case in ("all", "gated"):
            # 2023 trail43: exact segment time is valid, but Torrås→Almered pace is gated.
            await page.locator('[data-family="trail43"]').click()
            await page.locator("#year-select").select_option("2023")
            await page.wait_for_function("document.querySelector('#race-title').textContent.includes('2023')")
            await select_two(page, data["data/races/2023-trail43.json"])
            gated = page.locator(".comparison-segment-table tbody tr").filter(has_text="Torrås → Almered")
            assert await gated.count() == 1
            gated_text = await gated.inner_text()
            assert "Dold · fysisk distans ej verifierad" in gated_text
            assert re.search(r"\d+:\d{2}", gated_text), gated_text
            field_tooltip = await page.locator('#duel-field-chart circle title').all_text_contents()
            assert any("Torrås → Almered" in text and "segmenttid mot fältmedian" in text for text in field_tooltip)
            await page.locator('[data-close="compare-dialog"]').click()

        # 2018 trail22 has fewer than two meaningful common intermediate anchors:
        # sparse mode must remain useful without inventing route/checkpoint data.
        if selected_case in ("all", "sparse"):
            await page.locator('[data-family="trail22"]').click()
            await page.locator("#year-select").select_option("2018")
            await page.wait_for_function("document.querySelector('#race-title').textContent.includes('2018')")
            race=data["data/races/2018-trail22.json"]
            boundary_ids={station["uid"] for station in race["stations"] if station.get("is_analysis_boundary") and not station.get("is_finish")}
            observed={row["id"]:set() for row in race["results"]}
            for split in race["splits"]:
                if split["station_uid"] in boundary_ids:
                    observed[split["result_id"]].add(split["station_uid"])
            finishers=[row for row in race["results"] if row["status"]=="FINISHED"]
            pair=min(((a,b) for i,a in enumerate(finishers) for b in finishers[i+1:]),key=lambda pair:len(observed[pair[0]["id"]]&observed[pair[1]["id"]]))
            assert len(observed[pair[0]["id"]]&observed[pair[1]["id"]])<2
            await select_two(page, race, pair)
            sparse = await page.locator(".comparison-sparse").inner_text()
            assert "Förenklad verklig resa" in sparse
            assert "inga kontroller fylls ut" in sparse
            assert await page.locator("#duel-map").count() == 0
            # Sharing is a comparison capability, not a route capability.
            assert await page.locator("#duel-share").count() == 1
            await page.locator("#duel-share").click()
            assert "compareA=" in page.url and "compareB=" in page.url,page.url
            segment_rows=await page.locator(".comparison-segment-table tbody tr").count()
            assert segment_rows <= len([s for s in race["stations"] if s.get("is_analysis_boundary")])
            all_boundaries={station["uid"] for station in race["stations"] if station.get("is_analysis_boundary")}
            common_observed=sum(1 for uid in all_boundaries if uid in observed[pair[0]["id"]] and uid in observed[pair[1]["id"]])
            # Finish was excluded from the pairing map above; both selected FINISHED
            # rows have its exact published split in this edition.
            expected_points=common_observed+1
            assert await page.locator("#duel-gap-chart circle").count() == expected_points
            dialog = page.locator("#compare-dialog")
            assert await dialog.evaluate("node=>node.scrollWidth<=node.clientWidth+1")
        assert not errors, errors
        assert not await page.evaluate("window.__missing||[]")
        await browser.close()
        print(f"PASS Comparison 2.0 evidence case: {selected_case}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
