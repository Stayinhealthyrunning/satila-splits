#!/usr/bin/env python3
"""Browser acceptance for choosing the same runner from multiple Sätila years."""
from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(os.getenv("SATILA_SITE", "docs"))


def fixtures():
    boot = json.loads((ROOT / "data" / "bootstrap.json").read_text(encoding="utf-8"))
    data = {"data/bootstrap.json": boot}
    for edition in boot["editions"]:
        path = ROOT / "data" / "races" / f"{edition['race_key']}.json"
        data[f"data/races/{path.name}"] = json.loads(path.read_text(encoding="utf-8"))
    return data


async def main():
    data = fixtures()
    markup = (ROOT / "index.html").read_text(encoding="utf-8")
    markup = re.sub(r"<link [^>]*>", "", markup)
    markup = re.sub(r"<script[^>]*>\s*</script>", "", markup)

    async with async_playwright() as playwright:
        options = {"headless": True}
        if Path("/usr/bin/chromium").exists():
            options.update(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        browser = await playwright.chromium.launch(**options)
        page = await browser.new_page(viewport={"width": 900, "height": 900})
        page.set_default_timeout(10000)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)

        await page.set_content(markup)
        await page.evaluate(
            """payload=>{
              window.__fixtures=payload;
              window.fetch=async url=>{
                const key=String(url),value=window.__fixtures[key];
                return {ok:value!==undefined,status:value===undefined?404:200,json:async()=>value};
              };
            }""",
            data,
        )
        await page.add_script_tag(content=(ROOT / "assets" / "multi-year-comparison.js").read_text(encoding="utf-8"))
        await page.add_script_tag(content=(ROOT / "assets" / "app.js").read_text(encoding="utf-8"))
        await page.wait_for_function("document.querySelector('#race-title').textContent.includes('2025')")

        assert await page.locator("#multi-year-year").input_value() == "all"

        await page.locator("#multi-year-search").fill("Petra Klevmar")
        await page.wait_for_function("document.querySelectorAll('#multi-year-suggestions [data-multi-year-add]').length >= 4")
        option_2025 = page.locator("#multi-year-suggestions [data-multi-year-add]").filter(has_text="2025").first
        await option_2025.click()

        await page.locator("#multi-year-search").fill("Petra Klevmar")
        await page.wait_for_function("document.querySelectorAll('#multi-year-suggestions [data-multi-year-add]').length >= 3")
        option_2024 = page.locator("#multi-year-suggestions [data-multi-year-add]").filter(has_text="2024").first
        await option_2024.click()

        chips = await page.locator("#multi-year-selected").inner_text()
        assert "Petra Klevmar" in chips and "2025" in chips and "2024" in chips, chips
        assert not await page.locator("#open-multi-year-comparison").is_disabled()
        await page.locator("#open-multi-year-comparison").click()
        await page.wait_for_selector("#multi-year-dialog[open]")

        dialog = await page.locator("#multi-year-dialog-body").inner_text()
        assert dialog.count("Petra Klevmar") == 2, dialog
        assert "Fältindex" in dialog, dialog
        assert "Passage- och segmentduell är avstängd" in dialog, dialog
        assert "rangordnas inte mot varandra" in dialog, dialog
        assert "A snabbare med" not in dialog and "B snabbare med" not in dialog, dialog

        # The year filter must narrow search without discarding already selected cross-year results.
        await page.locator("#close-multi-year-dialog").click()
        await page.locator("#multi-year-year").select_option("2023")
        await page.locator("#multi-year-search").fill("Petra Klevmar")
        await page.wait_for_function("document.querySelectorAll('#multi-year-suggestions [data-multi-year-add]').length === 1")
        narrowed = await page.locator("#multi-year-suggestions").inner_text()
        assert "2023" in narrowed and "2022" not in narrowed and "2024" not in narrowed, narrowed

        assert not errors, errors
        await browser.close()
        print("PASS Sätila multi-year comparison", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
