#!/usr/bin/env python3
"""Static publication privacy gate for Sätila Splits.

Names/finishing results already public in the official timing source may be
shown, but raw participant activities, contact details and source SQLite must
not be copied into GitHub Pages. Runner pictures from social media are excluded
by the project owner's explicit design decision.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"docs"
BANNED={".gpx",".tcx",".fit",".kmz",".kml",".sqlite",".db",".zip",".tar",".gz",".csv",".xlsx",".parquet",".log",".env"}
RESULT_FIELDS={"id","source_uid","name","bib","sex","age","class_name","club","status","finish_seconds","place"}
SPLIT_FIELDS={"result_id","station_uid","elapsed_seconds","place"}
SENSITIVE={"email","e_mail","phone","telefon","mobile","address","adress","birthdate","personnummer","ip_address",
           "raw_json","access_token","refresh_token","private_track","location_history","gps_track"}

def main():
    assert ROOT.is_dir(),ROOT
    paths=[p for p in ROOT.rglob("*") if p.is_file()]
    forbidden=[str(p) for p in paths if p.suffix.lower() in BANNED]
    assert not forbidden,f"Do not publish raw/archive/private assets: {forbidden}"
    assert all(not p.name.lower().startswith((".env","secrets")) for p in paths)
    race_files=list((ROOT/"data"/"races").glob("*.json"))
    assert len(race_files)==27
    for f in race_files:
        race=json.loads(f.read_text(encoding="utf-8"))
        for r in race["results"]:
            extras=set(r)-RESULT_FIELDS
            assert not extras,f"Unexpected exported athlete field {extras} in {f}"
            assert not any(k.lower() in SENSITIVE for k in r),f
        for s in race["splits"]:
            extras=set(s)-SPLIT_FIELDS
            assert not extras,f"Unexpected exported split field {extras} in {f}"
    # This is a check of the distributed frontend rather than a claim that all
    # remote requests are impossible. Public event source links remain allowed.
    for p in (ROOT/"index.html", ROOT/"assets"/"app.js", ROOT/"assets"/"analytics-extra.js"):
        text=p.read_text(encoding="utf-8").lower()
        for pattern in (r'<img\b[^>]*\bsrc=[\'\"]https?://',
                        r'(?:instagram\.com|facebook\.com|strava\.com)/[^\s\'\"]+\.(?:jpe?g|png|webp)',
                        r'fetch\s*\(\s*[\'\"]https?://[^\'\"]+/(?:athletes|profiles|users)/'):
            assert not re.search(pattern,text),f"Potential external runner image/profile in {p}: {pattern}"
    routes=list((ROOT/"data"/"routes").glob("*.json"))
    inventory=json.loads((ROOT/"data"/"route-inventory.json").read_text(encoding="utf-8"))
    assert len(routes)==len(inventory) and len(routes)>=5
    assert len([v for v in inventory if v.get("type")=="OFFICIAL_ORGANIZER"])==5
    for f in routes:
        route=json.loads(f.read_text(encoding="utf-8"))
        assert all(len(point)==4 and all(isinstance(v,(int,float,type(None))) for v in point)
                   for point in route["points"]),"Route must contain sanitized geometry only"
        assert not (set(route)&SENSITIVE)
    print(f"PUBLICATION PRIVACY CHECKS PASSED: {len(race_files)} sanitized race bundles; {len(routes)} sanitized display routes; no raw GPS/database or social profile-image asset")

if __name__=="__main__":
    main()
