#!/usr/bin/env python3
"""Browser regression for all seven year-scoped historical Ultra85 maps."""
from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path

from playwright.async_api import async_playwright


ROOT = Path(os.getenv("SATILA_SITE", "docs"))
YEARS = (2018, 2019, 2021, 2022, 2023, 2024, 2025)
POINTS = {2018: 1618, 2019: 1345, 2021: 964, 2022: 1607, 2023: 796, 2024: 1158, 2025: 856}


async def main():
    bootstrap = json.loads((ROOT / "data/bootstrap.json").read_text(encoding="utf-8"))
    editions = {edition["race_key"]: edition for edition in bootstrap["editions"]}
    fixtures = {}
    for path in (ROOT / "data").glob("*.json"):
        fixtures[f"data/{path.name}"] = json.loads(path.read_text(encoding="utf-8"))
    for path in (ROOT / "data/races").glob("*.json"):
        fixtures[f"data/races/{path.name}"] = json.loads(path.read_text(encoding="utf-8"))
    for path in (ROOT / "data/routes").glob("*.json"):
        fixtures[f"data/routes/{path.name}"] = json.loads(path.read_text(encoding="utf-8"))

    for year in YEARS:
        edition = editions[f"{year}-ultra85"]
        route = fixtures[f"data/{edition['route_file']}"]
        assert route["type"] == "VERIFIED_PARTICIPANT"
        assert route["edition_references"] == [year]
        assert len(route["points"]) == POINTS[year]
        assert all(point[3] is None for point in route["points"])

    markup = (ROOT / "index.html").read_text(encoding="utf-8")
    markup = re.sub(r"<link [^>]*>", "", markup)
    markup = re.sub(r"<script[^>]*>\s*</script>", "", markup)
    script = (ROOT / "assets/app.js").read_text(encoding="utf-8")
    base_css = (ROOT / "assets/style.css").read_text(encoding="utf-8")
    extra_css = (ROOT / "assets/style-extra.css").read_text(encoding="utf-8")

    async with async_playwright() as playwright:
        options = {"headless": True}
        if Path("/usr/bin/chromium").exists():
            options.update(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        browser = await playwright.chromium.launch(**options)
        try:
            for width, height in ((1440, 900), (390, 844)):
                page = await browser.new_page(viewport={"width": width, "height": height})
                page.set_default_timeout(10000)
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                await page.set_content(markup)
                await page.add_style_tag(content=base_css)
                await page.add_style_tag(content=extra_css)
                await page.evaluate(
                    """data=>{
                      window.__fixtures=data;window.__missing=[];
                      window.fetch=async url=>{
                        const value=window.__fixtures[String(url)];
                        if(value===undefined)window.__missing.push(String(url));
                        return {ok:value!==undefined,status:value===undefined?404:200,json:async()=>value};
                      };
                    }""",
                    fixtures,
                )
                await page.add_script_tag(content=script)
                await page.locator('[data-family="ultra85"]').click()

                for year in YEARS:
                    edition = editions[f"{year}-ultra85"]
                    route = fixtures[f"data/{edition['route_file']}"]
                    await page.locator("#year-select").select_option(str(year))
                    await page.wait_for_function(
                        """expected=>{
                          const title=document.querySelector('#race-title')?.textContent||'';
                          const hit=document.querySelector('#course-map [data-map-hit]');
                          return title.includes(String(expected.year)) && hit &&
                            Math.abs(Number(hit.getAttribute('aria-valuemax'))-expected.length)<.001;
                        }""",
                        arg={"year": year, "length": route["geometry_length_km"]},
                    )
                    assert await page.locator("#course-map .route-base").count() == 1, (width, year)
                    assert await page.locator("#course-map .osm-attribution").count() == 1, (width, year)
                    assert await page.locator("#course-elevation .elev-line").count() == 0, (width, year)
                    elevation_copy = await page.locator("#course-elevation").inner_text()
                    assert "Höjddata saknas" in elevation_copy, (width, year, elevation_copy)
                    source_copy = await page.locator("#course-source").inner_text()
                    assert "deltagar" in source_copy.lower(), (width, year, source_copy)

                    hit = page.locator("#course-map [data-map-hit]")
                    await hit.focus()
                    await page.keyboard.press("ArrowRight")
                    await page.wait_for_function(
                        """()=>Number(document.querySelector('#course-map [data-map-hit]')?.getAttribute('aria-valuenow'))>0""",
                    )
                    overflow = await page.evaluate(
                        "document.documentElement.scrollWidth-document.documentElement.clientWidth"
                    )
                    assert overflow <= 1, (width, year, overflow)
                    print(
                        f"PASS {width}px {year}/Ultra85: map works, elevation absence explicit, no overflow",
                        flush=True,
                    )

                assert not errors, (width, errors)
                assert not await page.evaluate("window.__missing"), (
                    width,
                    await page.evaluate("window.__missing"),
                )
                await page.close()
        finally:
            await browser.close()

    print("PASS: Ultra85 2018, 2019 and 2021–2025 historical route regression")


if __name__ == "__main__":
    asyncio.run(main())
