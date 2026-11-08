#!/usr/bin/env python3
"""Real-browser regression: 2026 ultra depot map and illustrative replay.

The official EQ source station TIME/Total positions remain unchanged. Only
route display markers and interpolated progress are corrected. No private FIT
or unfiltered participant data are accessed by this test.
"""
import asyncio
import json
import os
import re
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(os.getenv("SATILA_SITE", "docs"))
EXPECTED = [
    ("Navåsen", 22.7, 22.775063),
    ("Helsjön", 37.8, 37.969581),
    ("Äskhult", 54.6, 54.694012),
    ("Fjärås", 63.4, 63.435171),
    ("Lerbäck", 72.8, 72.843690),
    ("Ramhultafallet", 81.4, 81.696055),
]


def fixture():
    root = ROOT / "data"
    manifest = json.loads((root / "bootstrap.json").read_text(encoding="utf-8"))
    data = {"data/bootstrap.json": manifest}
    for p in root.glob("*.json"):
        data[f"data/{p.name}"] = json.loads(p.read_text(encoding="utf-8"))
    for p in (root / "races").glob("*.json"):
        data[f"data/races/{p.name}"] = json.loads(p.read_text(encoding="utf-8"))
    for p in (root / "routes").glob("*.json"):
        data[f"data/routes/{p.name}"] = json.loads(p.read_text(encoding="utf-8"))
    return data


async def main():
    data = fixture()
    route = data["data/routes/ultra85-2026.json"]
    race = data["data/races/2026-ultra85.json"]
    assert len(route["aid_stations"]) == 6
    assert [(s["name"], s["official_km"], s["route_km"]) for s in route["aid_stations"]] == EXPECTED
    assert len(race["stations"]) == 8, "Do not synthesize official EQ timing rows"
    assert not any(x["name"] in ("Helsjön", "Fjärås") for x in race["stations"])
    # An existing public adult finisher with published TIME at both bounding
    # official checkpoints; the person's name/ID is not printed to CI logs.
    by_result = {}
    for sp in race["splits"]:
        by_result.setdefault(sp["result_id"], set()).add(sp["station_uid"])
    runner = next(x for x in race["results"] if x["status"] == "FINISHED" and
                  {1454180, 1454198}.issubset(by_result.get(x["id"], set())))

    markup = re.sub(r"<script[^>]*>\s*</script>", "",
                    (ROOT / "index.html").read_text(encoding="utf-8"))
    markup = re.sub(r"<link [^>]*>", "", markup)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            for width, height in ((1280, 900), (390, 844)):
                page = await browser.new_page(viewport={"width": width, "height": height})
                errors = []
                page.on("pageerror", lambda err: errors.append(str(err)))
                await page.set_content(markup)
                for style in ("style.css", "style-extra.css"):
                    path = ROOT / "assets" / style
                    if path.exists():
                        await page.add_style_tag(content=path.read_text(encoding="utf-8"))
                await page.evaluate("""fixtures=>{
                    window.__fixtures=fixtures;
                    window.fetch=async url=>{
                        let x=window.__fixtures[String(url)];
                        return {ok:x!==undefined,status:x!==undefined?200:404,json:async()=>x};
                    };
                }""", data)
                await page.add_script_tag(content=(ROOT/"assets/profile-analysis.js").read_text(encoding="utf-8"))
                await page.add_script_tag(content=(ROOT/"assets/app.js").read_text(encoding="utf-8"))
                await page.locator('[data-family="ultra85"]').click()
                await page.locator("#year-select").select_option("2026")
                await page.wait_for_function(
                    "document.querySelector('#race-title')?.textContent.includes('85 km · 2026')")
                await page.wait_for_function(
                    "document.querySelectorAll('#course-map [data-aid]').length===6")
                for name, official, km in EXPECTED:
                    marker = page.locator(f'#course-map [data-aid="{name}"]')
                    assert await marker.count() == 1, (width, name, "missing map stop")
                    route_km = float(await marker.get_attribute("data-route-km"))
                    assert abs(route_km - km) < .00001, (width, name, route_km)
                    assert await page.locator(
                        f'#course-elevation [data-aid-elevation="{name}"]').count() == 1, (
                        width, name, "missing elevation marker")
                    assert str(round(official, 1)).replace(".", ",") in (
                        await marker.locator("title").inner_text()), name

                # Show a real published finisher's personal 2026 replay.
                await page.locator("#runner-search").fill(runner["name"])
                await page.locator("#runner-suggestions .suggestion").first.click()
                await page.wait_for_selector("#profile-replay-range")
                async def seek(km):
                    await page.locator("#profile-replay-range").evaluate(
                        """(node,value)=>{
                            node.value=String(value);
                            node.dispatchEvent(new Event('input',{bubbles:true}))
                        }""", km)
                    return await page.locator('[data-profile-live="segment"]').inner_text()

                assert await seek(35.6) == "Navåsen → Helsjön", (width, "35.6 replay segment")
                assert await seek(50.0) == "Helsjön → Äskhult", (width, "50 replay segment")
                assert await seek(60.0) == "Äskhult → Fjärås", (width, "60 replay segment")
                assert await seek(70.0) == "Fjärås → Lerbäck", (width, "70 replay segment")
                assert await seek(77.0) == "Lerbäck → Ramhultafallet", (width, "77 replay segment")
                assert await page.locator(
                    '#profile-mini-map [data-aid="Ramhultafallet"]').count() == 1
                assert await page.locator(
                    '#profile-mini-elev [data-aid-elevation="Ramhultafallet"]').count() == 1
                assert not errors, (width, "JS errors", errors[:4])
                await page.close()
            print("PASS 2026 ultra: six depots, Ramhulta near named landmark, elevation and replay on mobile/desktop",
                  flush=True)
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
