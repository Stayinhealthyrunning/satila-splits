#!/usr/bin/env python3
"""Fetch public Sätila Trail GPX research sources without committing them.

The artifact is for verification/analysis. Third-party coordinate data is not
automatically republished in the public repository.
"""
from __future__ import annotations

import hashlib
import io
import json
import pathlib
import urllib.parse
import urllib.request
import zipfile

OUT = pathlib.Path("research-artifacts")
OUT.mkdir(exist_ok=True)

UA = "satila-splits-research/1.0"

def request(url: str, *, data: bytes | None = None, headers: dict | None = None) -> bytes:
    h = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

manifest: list[dict] = []

# Official organizer ZIP for all 2026 courses.
zip_url = "https://www.satilatrail.se/wp-content/uploads/2026/09/satilatrail_gpx_2026.zip"
blob = request(zip_url)
zip_path = OUT / "satilatrail_gpx_2026.zip"
zip_path.write_bytes(blob)
manifest.append({
    "source_class": "OFFICIAL_ORGANIZER",
    "url": zip_url,
    "filename": zip_path.name,
    "sha256": hashlib.sha256(blob).hexdigest(),
    "bytes": len(blob),
})

with zipfile.ZipFile(io.BytesIO(blob)) as zf:
    names = [n for n in zf.namelist() if not n.endswith("/")]
    for name in names:
        data = zf.read(name)
        safe = pathlib.Path(name).name
        target = OUT / f"official_2026_{safe}"
        target.write_bytes(data)
        manifest.append({
            "source_class": "OFFICIAL_ORGANIZER",
            "container": zip_path.name,
            "member": name,
            "filename": target.name,
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
        })

# Trace de Trail: known public/homologated course IDs.
trace_ids = {
    "trail43_2017": 39527,
    "ultra85_2026": 355873,
    "trail43_2026": 355874,
}
endpoint = "https://tracedetrail.fr/download/getFile/tracedetrail"
for label, trace_id in trace_ids.items():
    payload = urllib.parse.urlencode({
        "traceID": str(trace_id),
        "format": "gpx",
        "trace": "1",
        "pi": "1",
        "waytypes": "0",
        "devneg": "0",
        "devpos": "0",
        "distance": "0",
        "dir": "0",
    }).encode()
    raw = request(
        endpoint,
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/json,text/plain,*/*",
        },
    )
    response_path = OUT / f"tracedetrail_{trace_id}_response.json"
    response_path.write_bytes(raw)
    obj = json.loads(raw)
    gpx = (obj.get("gpx") or "").encode()
    entry = {
        "source_class": "ITRA_TRACE",
        "trace_id": trace_id,
        "label": label,
        "endpoint": endpoint,
        "response_success": obj.get("success"),
        "message": obj.get("msg"),
    }
    if b"<gpx" in gpx:
        target = OUT / f"{label}_tracedetrail_{trace_id}.gpx"
        target.write_bytes(gpx)
        entry.update({
            "filename": target.name,
            "sha256": hashlib.sha256(gpx).hexdigest(),
            "bytes": len(gpx),
        })
    manifest.append(entry)

(OUT / "manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print(json.dumps(manifest, ensure_ascii=False, indent=2))
