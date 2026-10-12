#!/usr/bin/env python3
"""Reconcile public coverage counters after privacy withholding."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data"


def present(value: object) -> bool:
    return value is not None and str(value).strip() != ""


def main() -> None:
    path = DATA / "coverage.json"
    coverage = json.loads(path.read_text(encoding="utf-8"))
    for row in coverage:
        race = json.loads(
            (DATA / "races" / f"{row['race_key']}.json").read_text(encoding="utf-8")
        )
        results = race["results"]
        row.update(
            results=len(results),
            finishers=sum(item.get("status") == "FINISHED" for item in results),
            dnf=sum(item.get("status") == "DNF" for item in results),
            dns=sum(item.get("status") == "DNS" for item in results),
            dsq=sum(item.get("status") == "DSQ" for item in results),
            unknown=sum(item.get("status") == "UNKNOWN" for item in results),
            split_observations=len(race["splits"]),
            sex_f=sum(item.get("sex") == "F" for item in results),
            sex_m=sum(item.get("sex") == "M" for item in results),
            sex_known=sum(item.get("sex") in {"F", "M"} for item in results),
            age_known=sum(present(item.get("age")) for item in results),
            class_known=sum(present(item.get("class_name")) for item in results),
            club_known=sum(present(item.get("club")) for item in results),
            status_known=sum(item.get("status") != "UNKNOWN" for item in results),
            known_starters=sum(item.get("status") in {"FINISHED", "DNF", "DSQ"} for item in results),
        )
    path.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Reconciled {len(coverage)} public coverage rows")


if __name__ == "__main__":
    main()
