#!/usr/bin/env python3
"""Compare original published browser JSON with an independently rebuilt copy.

The only permitted metadata normalization is a user-owned archive's normalized
ASCII spelling in route-inventory.source_filename, provided every other route
attribute (including raw source SHA-256) is *identical*. The script does not
inspect or output athlete names, raw contestant JSON or personal metadata.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

def json_hashes(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*.json")}

def verify(published,rebuilt):
    published,rebuilt=Path(published),Path(rebuilt)
    expected=json_hashes(published)
    actual=json_hashes(rebuilt)
    failures=[]
    if set(expected)!=set(actual):
        failures.append(f"Missing published files: {sorted(set(expected)-set(actual))}; extra reconstructed files: {sorted(set(actual)-set(expected))}")
    differences=sorted(k for k in expected.keys()&actual.keys() if expected[k]!=actual[k])
    normalized=[]
    for path in differences:
        if path!="route-inventory.json":
            failures.append(f"JSON content checksum differs: {path}")
            continue
        a=json.loads((published/path).read_text(encoding="utf-8"))
        b=json.loads((rebuilt/path).read_text(encoding="utf-8"))
        aa={r["family"]:{k:v for k,v in r.items() if k!="source_filename"} for r in a}
        bb={r["family"]:{k:v for k,v in r.items() if k!="source_filename"} for r in b}
        if len(aa)!=len(a) or len(bb)!=len(b) or aa!=bb:
            failures.append("Route inventory differs beyond the source_filename spelling")
            continue
        for family in aa:
            if a[[r["family"] for r in a].index(family)]["source_sha256"]!=bb[family]["source_sha256"]:
                failures.append(f"Route {family}: raw source checksum differs")
        normalized.append(path)
    summary={"schema":"satila-rebuild-parity-v1",
        "published_json_files":len(expected),"rebuilt_json_files":len(actual),
        "byte_identical_files":len(expected.keys()&actual.keys())-len(differences),
        "filename_only_normalized_files":normalized,
        "route_source_sha256_preserved":bool(normalized) and not failures,
        "pass":not failures,"failures":failures}
    return summary

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--published",required=True,type=Path)
    parser.add_argument("--rebuilt",required=True,type=Path)
    parser.add_argument("--report",type=Path)
    args=parser.parse_args()
    result=verify(args.published,args.rebuilt)
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
    raise SystemExit(0 if result["pass"] else 1)

if __name__=="__main__":
    main()
