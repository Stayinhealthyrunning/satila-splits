#!/usr/bin/env python3
"""Optional independent rebuild against the committed public Sätila JSON set.

Use a PRIVATE unpacked EQ Timing source and the five original organizer GPX.
The source is never copied into docs/, committed, or uploaded. The GPX copies
are assigned stable publication filenames BY CONTENT DIGEST only. All generated
JSON Git-blob identities must agree with the target published directory.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
EXPECTED={
 "304fe04cba9ae22840253a99589fe142c31971ee129cc3fb38dde0ecfbc7144d":"Sätila Trail 5 - 2026.gpx",
 "24fc6f0ff6eca90dade4471e4743dccbed2272c02fe88b6619c46c6ece9d7c91":"Sätila Trail 10 - 2026.gpx",
 "c78872ddd3d9e0575eb260227a2d9b40455d7841d0d8a4dcfe71614356a06c39":"Sätila Trail 21 - 2026.gpx",
 "4b10bee2201e8f2493a1bf564c1603c5431c123fdc8d19dfb432655fb04ee827":"Sätila Trail 43 - 2026.gpx",
 "c5c313faf2b137cfeacf3b90cee4638094070793d70c8a88ca00944360f582c0":"Sätila Trail 85 - 2026.gpx",
}

def blob_digest(binary):
    return hashlib.sha1(("blob "+str(len(binary))+"\0").encode("ascii")+binary).hexdigest()

def blobs(root):
    return {str(p.relative_to(root)):blob_digest(p.read_bytes()) for p in root.rglob("*.json") if p.is_file()}

def rebuild(source,original_gpx,events,published,report_output=None):
    if not (source/"summary.json").is_file():
        raise ValueError("Expected full frozen EQ root directory containing summary.json")
    files=list(original_gpx.glob("*.gpx"))
    if len(files)<5:
        raise ValueError("Five original checksum-locked organizer GPX files are required")
    found={}
    with tempfile.TemporaryDirectory(prefix="satila-independent-rebuild-") as tmp:
        tmp=pathlib.Path(tmp)
        canonical=tmp/"gpx";canonical.mkdir()
        for raw in files:
            b=raw.read_bytes()
            digest=hashlib.sha256(b).hexdigest()
            if digest in EXPECTED:
                if digest in found:raise ValueError("Duplicate source GPX checksum: "+digest)
                found[digest]=raw.name
                # Rename a temporary COPY, never modify original raw source.
                (canonical/EXPECTED[digest]).write_bytes(b)
        if set(found)!=set(EXPECTED):
            raise ValueError("Source GPX SHA-256 changed or files missing: "+repr(sorted(set(EXPECTED)-set(found))))
        out=tmp/"new-publication"
        command=[sys.executable,str(ROOT/"tools"/"build_satila.py"),
                 "--source",str(source),"--gpix",str(canonical),
                 "--events",str(events),"--out",str(out)]
        subprocess.run(command,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        rebuilt=blobs(out)
        committed=blobs(published)
        missing=sorted(committed.keys()-rebuilt.keys())
        extra=sorted(rebuilt.keys()-committed.keys())
        different=sorted(k for k in rebuilt.keys() & committed.keys()
                         if rebuilt[k]!=committed[k])
        sums=json.loads((out/"bootstrap.json").read_text(encoding="utf-8"))
        summary={
            "schema":"satila-independent-rebuild-v1",
            "baseline_directory":str(published),
            "published_json":len(committed),
            "rebuilt_json":len(rebuilt),
            "exact_git_blob_matches":len(set(committed)&set(rebuilt))-len(different),
            "missing":missing,"extra":extra,"different":different,
            "edition_count":len(sums["editions"]),
            "results":sum(e["results"] for e in sums["editions"]),
            "finishers":sum(e["finishers"] for e in sums["editions"]),
            "real_time_splits":sum(e["split_observations"] for e in sums["editions"]),
            "organizer_gpx_verified":len(found),
            "result":"PASS" if not (missing or extra or different) else "FAIL",
        }
        if report_output:
            pathlib.Path(report_output).write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        return summary

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source",type=pathlib.Path,required=True,help="PRIVATE original EQ Timing eqtiming-full directory")
    ap.add_argument("--original-gpx",type=pathlib.Path,required=True,help="PRIVATE directory with the 5 raw official GPX")
    ap.add_argument("--events",type=pathlib.Path,default=ROOT/"config"/"eqtiming-events.json")
    ap.add_argument("--published",type=pathlib.Path,default=ROOT/"docs"/"data")
    ap.add_argument("--report",type=pathlib.Path,help="Optional PUBLIC-safe metadata-only verification report")
    args=ap.parse_args()
    result=rebuild(args.source,args.original_gpx,args.events,args.published,args.report)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if result["result"]!="PASS":raise SystemExit(1)

if __name__=="__main__":
    main()
