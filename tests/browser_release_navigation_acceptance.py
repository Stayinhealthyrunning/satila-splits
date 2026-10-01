#!/usr/bin/env python3
"""Release-only browser acceptance for deep links, Back/Forward and focus.

Not wired into green audit CI yet because the first-draft app uses
history.replaceState for edition changes; Codex release candidate must promote
user-initiated race/year changes to navigable history entries.
"""
import asyncio,json,os,re
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path(os.getenv("SATILA_SITE","docs"))

def payload():
    boot=json.loads((ROOT/"data/bootstrap.json").read_text(encoding="utf-8"))
    data={"data/bootstrap.json":boot}
    for ed in boot["editions"]:
        p=ROOT/"data/races"/f"{ed['race_key']}.json"
        data["data/races/"+p.name]=json.loads(p.read_text(encoding="utf-8"))
    for p in (ROOT/"data/routes").glob("*.json"):
        data["data/routes/"+p.name]=json.loads(p.read_text(encoding="utf-8"))
    return data

async def main():
    fixtures=payload()
    html=(ROOT/"index.html").read_text(encoding="utf-8")
    html=re.sub(r"<link [^>]*>","",html)
    html=re.sub(r"<script[^>]*>\s*</script>","",html)
    js=(ROOT/"assets/app.js").read_text(encoding="utf-8")
    css=(ROOT/"assets/style.css").read_text(encoding="utf-8")
    extra=(ROOT/"assets/style-extra.css").read_text(encoding="utf-8")
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(headless=True)
        try:
            page=await browser.new_page(viewport={"width":390,"height":844},reduced_motion="reduce")
            errors=[]
            page.on("pageerror",lambda e:errors.append(str(e)))
            await page.set_content(html)
            await page.add_style_tag(content=css)
            await page.add_style_tag(content=extra)
            await page.evaluate("""data=>{
              window.__fixtures=data;
              window.fetch=async u=>{
                let x=window.__fixtures[String(u)];
                return {ok:x!==undefined,status:x===undefined?404:200,json:async()=>x};
              };
              history.replaceState(null,'','#family=trail43&year=2023');
            }""",fixtures)
            await page.add_script_tag(content=js)
            await page.wait_for_function("document.querySelector('#race-title').textContent.includes('43 km · 2023')")
            # Deep link is the initial state and remains shareable.
            assert "family=trail43" in page.url and "year=2023" in page.url,page.url
            # User changes must create a navigable state, not erase prior edition.
            await page.locator("#year-select").select_option("2024")
            await page.wait_for_function("document.querySelector('#race-title').textContent.includes('2024')")
            assert "year=2024" in page.url,page.url
            await page.locator('[data-family="trail22"]').click()
            await page.wait_for_function("document.querySelector('#race-title').textContent.includes('22 km')")
            chosen=await page.locator("#race-title").inner_text()
            assert "family=trail22" in page.url,page.url
            # Browser Back must restore the prior actual race selection.
            await page.go_back()
            await page.wait_for_function("document.querySelector('#race-title').textContent.includes('43 km · 2024')")
            assert await page.locator("#year-select").input_value()=="2024"
            await page.go_back()
            await page.wait_for_function("document.querySelector('#race-title').textContent.includes('43 km · 2023')")
            # Browser Forward must redo selection.
            await page.go_forward()
            await page.wait_for_function("document.querySelector('#race-title').textContent.includes('43 km · 2024')")
            # Keyboard focus and reduced motion are observable.
            await page.locator(".skip-link").focus()
            self_focus=await page.evaluate("document.activeElement.classList.contains('skip-link')")
            assert self_focus
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(50)
            assert await page.evaluate("location.hash.includes('main') || document.activeElement.id==='main'")
            transition=await page.locator(".race-card").evaluate("e=>getComputedStyle(e).transitionDuration")
            assert transition in ("0s","0ms",""),transition
            await page.locator("#menu-toggle").focus()
            await page.keyboard.press("Enter")
            assert await page.locator("#menu-toggle").get_attribute("aria-expanded")=="true"
            await page.keyboard.press("Escape")
            # Escape behavior for native dialog is browser-provided; verify own Help dialog.
            await page.locator(".info").first.click()
            assert await page.locator("#help-dialog").evaluate("d=>d.open")
            await page.keyboard.press("Escape")
            assert not await page.locator("#help-dialog").evaluate("d=>d.open")
            assert not errors,errors
            print("RELEASE NAVIGATION/A11Y ACCEPTANCE PASSED",chosen,flush=True)
        finally:
            await browser.close()

if __name__=="__main__":
    asyncio.run(main())
