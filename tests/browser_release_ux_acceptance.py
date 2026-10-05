#!/usr/bin/env python3
"""Release-only UX acceptance: keyboard search/focus, mobile menu and data errors.

Not included in the green source audit before Codex integration because the
first draft does not yet meet every release UX expectation.
"""
import asyncio,json,os,re
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path(os.getenv("SATILA_SITE","docs"))

def data_payload():
    boot=json.loads((ROOT/"data/bootstrap.json").read_text(encoding="utf-8"))
    data={"data/bootstrap.json":boot}
    for e in boot["editions"]:
        p=ROOT/"data/races"/f"{e['race_key']}.json"
        data["data/races/"+p.name]=json.loads(p.read_text(encoding="utf-8"))
    for p in (ROOT/"data/routes").glob("*.json"):
        data["data/routes/"+p.name]=json.loads(p.read_text(encoding="utf-8"))
    return data

async def build_page(browser,fixtures,width=390,height=844):
    markup=(ROOT/"index.html").read_text(encoding="utf-8")
    markup=re.sub(r"<link [^>]*>","",markup)
    markup=re.sub(r"<script[^>]*>\s*</script>","",markup)
    page=await browser.new_page(viewport={"width":width,"height":height})
    await page.set_content(markup)
    await page.add_style_tag(content=(ROOT/"assets/style.css").read_text(encoding="utf-8"))
    extra=ROOT/"assets/style-extra.css"
    if extra.exists():await page.add_style_tag(content=extra.read_text(encoding="utf-8"))
    await page.evaluate("""d=>{
      window.__fixtures=d;
      window.__failRace=null;
      window.fetch=async u=>{
        const key=String(u);
        if(window.__failRace && key.includes(window.__failRace))
          return {ok:false,status:503,json:async()=>({})};
        const x=window.__fixtures[key];
        return {ok:x!==undefined,status:x===undefined?404:200,json:async()=>x};
      };
    }""",fixtures)
    await page.add_script_tag(content=(ROOT/"assets/profile-analysis.js").read_text(encoding="utf-8"))
    await page.add_script_tag(content=(ROOT/"assets/app.js").read_text(encoding="utf-8"))
    await page.wait_for_function("document.querySelector('#race-title').textContent.includes('2025')")
    return page

async def main():
    fixtures=data_payload()
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(headless=True)
        try:
            page=await build_page(browser,fixtures)
            page.set_default_timeout(7000)

            # Mobile navigation: keyboard Enter opens, Escape must close and update ARIA.
            menu=page.locator("#menu-toggle")
            await menu.focus()
            await page.keyboard.press("Enter")
            assert await menu.get_attribute("aria-expanded")=="true"
            assert await page.locator("#primary-nav").evaluate("n=>n.classList.contains('open')")
            await page.keyboard.press("Escape")
            assert await menu.get_attribute("aria-expanded")=="false","Escape must collapse mobile navigation"
            assert not await page.locator("#primary-nav").evaluate("n=>n.classList.contains('open')")

            # Keyboard autocomplete: no mouse needed to open runner profile.
            race=fixtures["data/races/2025-trail43.json"]
            runner=next(r for r in race["results"] if r["status"]=="FINISHED" and r.get("name"))
            search=page.locator("#runner-search")
            await search.fill(runner["name"][:max(3,len(runner["name"].split()[0]))])
            await page.wait_for_function("document.querySelectorAll('#runner-suggestions .suggestion').length>0")
            await search.focus()
            await page.keyboard.press("ArrowDown")
            active=await page.evaluate("document.activeElement?.classList.contains('suggestion')")
            assert active,"ArrowDown must move active focus to a suggestion"
            await page.keyboard.press("Enter")
            await page.wait_for_function("document.querySelector('#profile-dialog').open")
            close=page.locator('[data-close="profile-dialog"]')
            await close.click()
            assert not await page.locator("#profile-dialog").evaluate("d=>d.open")
            # Browser/native dialog should restore focus to the invoking suggestion
            # or a stable search control; do not dump focus on document body.
            focus_id=await page.evaluate("document.activeElement?.id || document.activeElement?.className || document.activeElement?.tagName")
            assert focus_id not in ("BODY","HTML",""),focus_id

            # Method dialog is named, keyboard accessible, Escape closes.
            info=page.locator(".info").first
            await info.focus()
            await page.keyboard.press("Enter")
            assert await page.locator("#help-dialog").evaluate("d=>d.open")
            await page.keyboard.press("Escape")
            assert not await page.locator("#help-dialog").evaluate("d=>d.open")

            # Missing edition bundle: user must receive a visible error/alert.
            await page.evaluate("window.__failRace='2025-trail43.json'")
            await page.locator('[data-family="trail43"]').click()
            await page.wait_for_timeout(250)
            visible=(await page.locator("body").inner_text()).lower()
            semantic_alert=await page.locator('[role="alert"]').count()
            acceptable=("kunde inte" in visible or "saknar data" in visible or "fel" in visible or semantic_alert>0)
            assert acceptable,"Race-load failure must be visible to the user, not only console.error"

            overflow=await page.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
            assert overflow<=1,overflow
            print("RELEASE UX ACCEPTANCE PASSED",flush=True)
            await page.close()
        finally:
            await browser.close()

if __name__=="__main__":
    asyncio.run(main())
