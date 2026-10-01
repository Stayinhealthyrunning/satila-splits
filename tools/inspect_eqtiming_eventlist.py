#!/usr/bin/env python3
"""Discover Sätila Trail editions through EQ Timing's own public event catalog."""
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
        await page.goto("https://events.eqtiming.com/eventlist",wait_until="domcontentloaded",timeout=60000)
        await page.wait_for_timeout(2500)
        # Use exactly the public API request shape used by EQ's own event-list UI.
        data=await page.evaluate("""async () => {
          const u = new URL('/api/Events', location.origin);
          const p = {query:'Sätila Trail',dateFrom:'2015-01-01',dateTo:'2026-12-31',
            organizationId:'0',regionIds:'',levelIds:'',sportIds:'',take:'1500',
            dateSort:'true',desc:'true',onlyValidated:'false',onlyshowfororganizer:'false',
            organizerIds:'',graded:'false',racequality:'false'};
          Object.entries(p).forEach(([k,v])=>u.searchParams.set(k,v));
          const r=await fetch(u); if(!r.ok) throw new Error('EQ Events '+r.status);
          return await r.json();
        }""")
        (OUT/"satila-events-raw.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        # Keep only records whose serialized public catalog data actually identifies Sätila.
        rows=data if isinstance(data,list) else next((v for v in data.values() if isinstance(v,list)),[])
        matches=[x for x in rows if "sätila" in json.dumps(x,ensure_ascii=False).lower() or "satila" in json.dumps(x,ensure_ascii=False).lower()]
        (OUT/"satila-events.json").write_text(json.dumps(matches,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(json.dumps(matches,ensure_ascii=False,indent=2))
        if not matches: raise SystemExit("EQ public event catalog returned no Sätila matches")
        await browser.close()

asyncio.run(main())
