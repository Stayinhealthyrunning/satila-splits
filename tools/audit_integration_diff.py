#!/usr/bin/env python3
"""Compare source/provenance surface between a verified baseline and candidate.

Designed for later Codex integration. Frontend files may change freely; race
bundles, route inventory, source fingerprints and immutable data configuration
must not change unless the integration explicitly declares a data migration.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

IMMUTABLE_GLOBS=(
 "docs/data/bootstrap.json",
 "docs/data/coverage.json",
 "docs/data/route-inventory.json",
 "docs/data/source-fingerprints.json",
 "docs/data/races/*.json",
 "docs/data/routes/*.json",
 "config/eqtiming-events.json",
 "config/course-versions.json",
)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def surface(root):
    root=Path(root)
    out={}
    for pattern in IMMUTABLE_GLOBS:
        for p in root.glob(pattern):
            if p.is_file():
                out[p.relative_to(root).as_posix()]=digest(p)
    return dict(sorted(out.items()))

def compare(base,candidate):
    a,b=surface(base),surface(candidate)
    return {
      "pass":a==b,
      "missing":sorted(set(a)-set(b)),
      "extra":sorted(set(b)-set(a)),
      "changed":sorted(k for k in set(a)&set(b) if a[k]!=b[k]),
      "baseline_files":len(a),
      "candidate_files":len(b),
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("baseline")
    p.add_argument("candidate")
    p.add_argument("--allow-data-change",action="store_true",
                   help="Report differences without failing; use only with explicit source/data migration review.")
    p.add_argument("--output")
    args=p.parse_args()
    result=compare(args.baseline,args.candidate)
    if args.output:
        Path(args.output).write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
    if not result["pass"] and not args.allow_data_change:
        raise SystemExit("Source/provenance surface changed: explicit data migration review required")

if __name__=="__main__":
    main()
