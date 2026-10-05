#!/usr/bin/env python3
"""Mark explicit class/sex contradictions as analytically unknown.

The original EQ Timing archive remains byte-identical. This migration only
updates the curated public bundle and then regenerates its coverage summary.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from build_satila import refresh_coverage


ROOT = Path(__file__).resolve().parents[1]
RACES = ROOT / "docs" / "data" / "races"


def explicit_class_sex(name: str | None) -> str | None:
    value = (name or "").strip().casefold()
    if re.match(r"^(kvinna|kvinnor|dam)(\b|\s|$)", value):
        return "F"
    if re.match(r"^(man|män|herr)(\b|\s|$)", value):
        return "M"
    return None


def main() -> None:
    changed = []
    for path in sorted(RACES.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        dirty = False
        for result in payload["results"]:
            class_sex = explicit_class_sex(result.get("class_name"))
            source_sex = result.get("sex")
            if source_sex in {"F", "M"} and class_sex and source_sex != class_sex:
                changed.append((payload["race_key"], result["id"], source_sex, result.get("class_name")))
                result["sex"] = None
                dirty = True
        if dirty:
            path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    refresh_coverage(ROOT / "docs" / "data")
    print(json.dumps({"normalized_conflicts": changed}, ensure_ascii=False))


if __name__ == "__main__":
    main()
