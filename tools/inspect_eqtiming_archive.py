#!/usr/bin/env python3
"""Inventory captured EQ Timing payloads and identify result-shaped JSON."""
from pathlib import Path
import argparse,json
ROOT=Path(__file__).resolve().parents[1]
def walk(x,path="$"):
    if isinstance(x,dict):
        keys={str(k).lower() for k in x}
        score=sum(any(t in k for k in keys) for t in ("name","bib","rank","place","time","result","class","distance"))
        if score>=3: yield path,score,sorted(keys)[:40]
        for k,v in x.items(): yield from walk(v,f"{path}.{k}")
    elif isinstance(x,list):
        for i,v in enumerate(x[:30]):yield from walk(v,f"{path}[{i}]")
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",default="data/work/eqtiming");args=ap.parse_args()
    root=ROOT/args.root; report=[]
    for p in root.glob("*/*.json"):
        if p.name=="manifest.json":continue
        try:o=json.loads(p.read_text(encoding="utf-8"))
        except Exception:continue
        hits=list(walk(o))
        report.append({"file":str(p.relative_to(ROOT)),"hits":[{"path":a,"score":b,"keys":c} for a,b,c in hits[:100]]})
    out=root/"payload-inventory.json";out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Inspected {len(report)} JSON payloads -> {out.relative_to(ROOT)}")
if __name__=="__main__":main()
