#!/usr/bin/env python3
"""Fetch and verify the organizer's official Sätila Trail 2026 GPX package.

The expected member checksums were independently recorded from the five files
supplied by the project owner on 2026-10-01. The organizer reuses its 2025
track files for the unchanged 2025→2026 courses at 5/10/21/43 km.
"""
from __future__ import annotations
import hashlib, io, pathlib, urllib.request, zipfile

URL="https://www.satilatrail.se/wp-content/uploads/2026/09/satilatrail_gpx_2026.zip"
OUT=pathlib.Path("data/source/gpx")
EXPECTED={
 "304fe04cba9ae22840253a99589fe142c31971ee129cc3fb38dde0ecfbc7144d":"Sätila Trail 5 - 2026.gpx",
 "24fc6f0ff6eca90dade4471e4743dccbed2272c02fe88b6619c46c6ece9d7c91":"Sätila Trail 10 - 2026.gpx",
 "c78872ddd3d9e0575eb260227a2d9b40455d7841d0d8a4dcfe71614356a06c39":"Sätila Trail 21 - 2026.gpx",
 "4b10bee2201e8f2493a1bf564c1603c5431c123fdc8d19dfb432655fb04ee827":"Sätila Trail 43 - 2026.gpx",
 "c5c313faf2b137cfeacf3b90cee4638094070793d70c8a88ca00944360f582c0":"Sätila Trail 85 - 2026.gpx",
}
req=urllib.request.Request(URL,headers={"User-Agent":"satila-splits-build/1.0","Accept":"application/zip,*/*"})
with urllib.request.urlopen(req,timeout=60) as r:
    blob=r.read()
OUT.mkdir(parents=True,exist_ok=True)
seen={}
with zipfile.ZipFile(io.BytesIO(blob)) as zf:
    for member in zf.namelist():
        if member.endswith("/") or not member.lower().endswith(".gpx"): continue
        raw=zf.read(member); digest=hashlib.sha256(raw).hexdigest()
        if digest in EXPECTED:
            target=OUT/EXPECTED[digest]; target.write_bytes(raw); seen[digest]=member
missing=set(EXPECTED)-set(seen)
if missing:
    raise SystemExit("Organizer ZIP no longer matches independently recorded GPX checksums: "+", ".join(sorted(missing)))
for digest,name in EXPECTED.items():
    print(f"verified {name}: {digest} from {seen[digest]}")
