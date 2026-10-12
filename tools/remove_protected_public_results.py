#!/usr/bin/env python3
"""Remove protected people and linked observations from Sätila browser data."""
from __future__ import annotations

import json
import statistics
from pathlib import Path

from privacy import DISPLAY_NAME, load_rules, normalize_name, record_is_suppressed

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs/data"
RULES = ROOT / "config/privacy-suppressions.json"


def write(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def main() -> None:
    rules = load_rules(RULES, require_private=True)
    removed_by_race: dict[str, dict[str, int]] = {}
    for path in sorted((DATA / "races").glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        removed = [
            row for row in payload["results"]
            if normalize_name(row.get("name")) == normalize_name(DISPLAY_NAME)
            or record_is_suppressed(row, rules, scope=payload["race_key"])
        ]
        removed_ids = {str(row["id"]) for row in removed}
        if not removed_ids:
            continue
        payload["results"] = [row for row in payload["results"] if str(row["id"]) not in removed_ids]
        payload["splits"] = [row for row in payload["splits"] if str(row["result_id"]) not in removed_ids]
        status_counts: dict[str, int] = {}
        for row in removed:
            status = str(row.get("status") or "UNKNOWN").upper()
            status_counts[status] = status_counts.get(status, 0) + 1
        removed_by_race[payload["race_key"]] = status_counts
        write(path, payload)

    bootstrap_path = DATA / "bootstrap.json"
    bootstrap = json.loads(bootstrap_path.read_text(encoding="utf-8"))
    coverage_path = DATA / "coverage.json"
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    race_files = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in (DATA / "races").glob("*.json")
    }
    for collection in (bootstrap.get("editions", []), coverage):
        for item in collection:
            race_key = item["race_key"]
            race = race_files[race_key]
            results = race["results"]
            item["results"] = len(results)
            item["finishers"] = sum(row.get("status") == "FINISHED" for row in results)
            item["dnf"] = sum(row.get("status") == "DNF" for row in results)
            item["dns"] = sum(row.get("status") == "DNS" for row in results)
            item["dsq"] = sum(row.get("status") == "DSQ" for row in results)
            item["unknown"] = sum(row.get("status") not in {"FINISHED", "DNF", "DNS", "DSQ"} for row in results)
            item["split_observations"] = len(race["splits"])
            finishes = [row["finish_seconds"] for row in results if row.get("status") == "FINISHED" and row.get("finish_seconds")]
            item["median_seconds"] = round(statistics.median(finishes), 2) if len(finishes) >= 5 else None
    write(bootstrap_path, bootstrap)
    write(coverage_path, coverage)
    total = sum(sum(value.values()) for value in removed_by_race.values())
    print(json.dumps({"status": "PASS", "removed_results": total, "affected_races": len(removed_by_race)}))


if __name__ == "__main__":
    main()
