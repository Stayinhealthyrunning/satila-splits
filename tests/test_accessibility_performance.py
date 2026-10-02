#!/usr/bin/env python3
"""Fast, deterministic Sätila release gates (stdlib only).

Run before expensive Chromium regression. This does not replace browser E2E.
"""
from __future__ import annotations
import gzip,json,os
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(os.getenv("SATILA_SITE",Path(__file__).resolve().parents[1]/"docs"))

class PageAudit(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids=[];self.dialogs=[];self.labels=[];self.controls=[];self.targets=[];self.headings=[];self._labels=[]
    def handle_starttag(self,tag,attrs):
        a={k:v or "" for k,v in attrs}
        if a.get("id"):self.ids.append(a["id"])
        if tag=="dialog":self.dialogs.append(a)
        if tag=="label":
            self._labels.append(True)
            if a.get("for"):self.labels.append(a["for"])
        if tag in ("input","select","textarea") and a.get("type")!="hidden":
            if not (a.get("aria-label") or a.get("aria-labelledby") or a.get("id") in self.labels or self._labels):
                self.controls.append((tag,a))
        if tag=="a" and a.get("href","").startswith("#") and len(a["href"])>1:self.targets.append(a["href"][1:])
        if tag=="h1":self.headings.append(tag)
    def handle_endtag(self,tag):
        if tag=="label" and self._labels:self._labels.pop()

def gz_size(p):
    return len(gzip.compress(p.read_bytes(),compresslevel=9,mtime=0))

def test_page_structure():
    page=PageAudit();html=(ROOT/"index.html").read_text(encoding="utf-8");page.feed(html)
    assert len(page.headings)==1,"Exactly one h1 required"
    assert len(set(page.ids))==len(page.ids),"Duplicate HTML id"
    assert not page.controls,f"Unlabelled controls: {page.controls}"
    assert set(page.targets).issubset(set(page.ids)),f"Broken anchors: {set(page.targets)-set(page.ids)}"
    assert len(page.dialogs)==4,"Expected profile, compare, map duel, method dialogs"
    for dialog in page.dialogs:
        label=dialog.get("aria-labelledby")
        assert dialog.get("aria-label") or label in page.ids,f"Unlabelled dialog: {dialog.get('id')}"
    assert 'aria-controls="primary-nav"' in html and 'id="primary-nav"' in html
    assert "https://www.instagram.com/" not in html,"Never hotlink social-media runner portraits"
    print("PASS accessibility: headings, IDs, form labels, named dialogs, navigation")

def test_budget():
    boot=ROOT/"data/bootstrap.json"
    assert gz_size(boot)<=10_240,f"Bootstrap >10KiB: {gz_size(boot)}"
    races=sorted((ROOT/"data/races").glob("*.json"))
    assert len(races)==27,f"Expected 27 editions, got {len(races)}"
    for p in races:
        assert p.stat().st_size<=600_000,f"Race >600kB raw: {p}"
        assert gz_size(p)<=75*1024,f"Race >75KiB gzip: {p}"
        obj=json.loads(p.read_text(encoding="utf-8"))
        assert len(obj["results"])==len({r["id"] for r in obj["results"]}),p
    js=gz_size(ROOT/"assets/app.js")
    css=gz_size(ROOT/"assets/style.css")
    extra=ROOT/"assets/style-extra.css"
    if extra.exists():css+=gz_size(extra)
    markup=gz_size(ROOT/"index.html")
    assert js<=256*1024,f"JS >256KiB gzip: {js}"
    assert css<=75*1024,f"CSS >75KiB gzip: {css}"
    assert markup<=32*1024,f"HTML >32KiB gzip: {markup}"
    hero=ROOT/"assets/hero.webp"
    assert hero.exists(),"Approved hero missing"
    initial=js+css+markup+gz_size(boot)+hero.stat().st_size
    assert initial<=512*1024,f"Critical initial transfer >512KiB: {initial}"
    print(f"PASS transfer budget: initial={initial}B, JS={js}B, CSS={css}B, HTML={markup}B; {len(races)} editions")

def test_coverage():
    boot=json.loads((ROOT/"data/bootstrap.json").read_text(encoding="utf-8"))
    coverage=json.loads((ROOT/"data/coverage.json").read_text(encoding="utf-8"))
    editions={e["race_key"]:e for e in boot["editions"]}
    assert len(coverage)==len(editions)==27
    for row in coverage:
        source=editions[row["race_key"]]
        assert row["results"]==source["results"]
        assert row["route_status"]==source["route_status"]
        assert row.get("route_file")==source.get("route_file")
        assert row["sex_known"]==row["sex_f"]+row["sex_m"]
        for field in ("sex_known","age_known","class_known","club_known","status_known","known_starters"):
            assert 0<=row[field]<=row["results"],(row["race_key"],field)
        if row.get("route_file"):
            assert len(row.get("route_sha256") or "")==64,row["race_key"]
            source_type=row.get("route_source_type")
            assert source_type in ("OFFICIAL_ORGANIZER","VERIFIED_PARTICIPANT"),row["race_key"]
            if source_type=="VERIFIED_PARTICIPANT":
                assert row["route_status"]=="participant_track_display_only",row["race_key"]
                display=json.loads((ROOT/"data"/row["route_file"]).read_text(encoding="utf-8"))
                assert display["edition_references"]==[row["year"]],row["race_key"]
                assert display["source_sha256"]==row["route_sha256"],row["race_key"]
    print("PASS coverage: 27 current editions, source fields and route status agree")

if __name__=="__main__":
    test_page_structure()
    test_budget()
    test_coverage()
