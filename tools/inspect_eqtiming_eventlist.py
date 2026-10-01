#!/usr/bin/env python3
"""Inspect EQ Timing's public historical event list for Sätila Trail."""
import asyncio, json
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/work/eqtiming-discovery"

async def main():
    OUT.mkdir(parents=True,exist_ok=True)
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        page=await browser.new_page(locale="sv-SE")
        responses=[]
        async def on_response(r):
            if "eqtiming" in r.url.lower() and ("event" in r.url.lower() or "api/" in r.url.lower()):
                responses.append({"url":r.url,"status":r.status,"content_type":r.headers.get("content-type","")})
        page.on("response",on_response)
        await page.goto("https://events.eqtiming.com/eventlist",wait_until="domcontentloaded",timeout=60000)
        await page.wait_for_timeout(5000)
        inputs=await page.locator("input").evaluate_all("""els => els.map(e => ({type:e.type,name:e.name,id:e.id,placeholder:e.placeholder,value:e.value,outer:e.outerHTML}))""")
        selects=await page.locator("select").evaluate_all("""els => els.map(e => ({name:e.name,id:e.id,outer:e.outerHTML}))""")
        links=await page.locator("a").evaluate_all("""els => els.map(e => ({text:(e.innerText||'').trim(),href:e.href})).filter(x=>/sätila|satila/i.test(x.text+x.href))""")
        body=await page.locator("body").inner_text()
        (OUT/"eventlist.html").write_text(await page.content(),encoding="utf-8")
        (OUT/"eventlist.txt").write_text(body,encoding="utf-8")
        (OUT/"diagnostic.json").write_text(json.dumps({"inputs":inputs,"selects":selects,"satila_links":links,"responses":responses},ensure_ascii=False,indent=2),encoding="utf-8")
        print(json.dumps({"inputs":inputs,"selects":selects,"satila_links":links,"responses":responses[-30:]},ensure_ascii=False,indent=2))
        await browser.close()

asyncio.run(main())
