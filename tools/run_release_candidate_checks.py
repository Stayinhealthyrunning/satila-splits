#!/usr/bin/env python3
"""One-command independent QA runner for the integrated Sätila release candidate.

Default is --source: deterministic/stdlib checks only. Use --browser only on a
candidate where Playwright Chromium is installed. --all runs both groups.
"""
from __future__ import annotations
import argparse,json,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=[
 ["python","tests/test_published_data_integrity.py"],
 ["python","tools/audit_segment_capabilities.py"],
 ["python","tools/audit_station_coverage.py"],
 ["python","tools/audit_segment_distance_capability.py"],
 ["python","tests/test_route_geometry_integrity.py"],
 ["python","tools/audit_ui_capabilities.py"],
 ["python","tests/test_publication_privacy.py"],
 ["python","-m","unittest","discover","-s","tests","-p","test_statistics_contract.py","-v"],
 ["python","-m","unittest","discover","-s","tests","-p","test_course_comparability_contract.py","-v"],
 ["python","-m","unittest","discover","-s","tests","-p","test_real_data_analysis_contract.py","-v"],
 ["python","-m","unittest","discover","-s","tests","-p","test_population_denominators.py","-v"],
 ["python","-m","unittest","discover","-s","tests","-p","test_public_summary_reconciliation.py","-v"],
 ["python","-m","unittest","discover","-s","tests","-p","test_source_chain_of_custody.py","-v"],
 ["python","tools/audit_historical_station_alignment.py"],
 ["python","-m","unittest","discover","-s","tests","-p","test_rebuild_parity_contract.py","-v"],
 ["python","-m","unittest","discover","-s","tests","-p","test_replay_source_contract.py","-v"],
 ["python","-m","unittest","discover","-s","tests","-p","test_golden_aggregate_regression.py","-v"],
 ["python","-m","unittest","discover","-s","tests","-p","test_review_package_contract.py","-v"],
 ["python","-m","unittest","discover","-s","tests","-p","test_integration_diff_contract.py","-v"],
 ["python","-m","unittest","discover","-s","tests","-p","test_component_readiness_manifest.py","-v"],
 ["python","-m","unittest","discover","-s","tests","-p","test_visual_asset_lock.py","-v"],
 ["python","tests/test_accessibility_performance.py"],
]
RELEASE_COPY=[["python","tests/test_release_copy_acceptance.py"]]
BROWSER=[
 ["python","tests/browser_synced_scrub_acceptance.py"],
 ["python","tests/browser_all_editions_acceptance.py"],
 ["python","tests/browser_evidence_acceptance.py"],
 ["python","tests/browser_release_navigation_acceptance.py"],
 ["python","tests/browser_release_ux_acceptance.py"],
 ["python","tests/browser_release_pace_capability_acceptance.py"],
]

def execute(commands):
    result=[]
    for cmd in commands:
        start=time.monotonic()
        print("\n>>>"," ".join(cmd),flush=True)
        p=subprocess.run(cmd,cwd=ROOT,text=True)
        row={"command":cmd,"returncode":p.returncode,"seconds":round(time.monotonic()-start,3)}
        result.append(row)
        if p.returncode:
            return result,False
    return result,True

def main():
    ap=argparse.ArgumentParser()
    g=ap.add_mutually_exclusive_group()
    g.add_argument("--source",action="store_true",help="Deterministic source/method/static checks (default)")
    g.add_argument("--browser",action="store_true",help="Playwright browser release checks only")
    g.add_argument("--all",action="store_true",help="Source + release copy + browser")
    g.add_argument("--plan",action="store_true",help="Print commands without executing")
    ap.add_argument("--json-output")
    args=ap.parse_args()
    if not any((args.source,args.browser,args.all,args.plan)):args.source=True
    commands=(SOURCE if args.source else BROWSER if args.browser else SOURCE+RELEASE_COPY+BROWSER if args.all else SOURCE+RELEASE_COPY+BROWSER)
    if args.plan:
        print(json.dumps({"source":SOURCE,"release_copy":RELEASE_COPY,"browser":BROWSER},ensure_ascii=False,indent=2))
        return
    rows,ok=execute(commands)
    out={"pass":ok,"commands":rows,"mode":"all" if args.all else "browser" if args.browser else "source"}
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("\nRELEASE CANDIDATE QA", "PASS" if ok else "FAIL",flush=True)
    raise SystemExit(0 if ok else 1)

if __name__=="__main__":
    main()
