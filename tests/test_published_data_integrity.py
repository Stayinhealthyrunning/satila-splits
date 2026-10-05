#!/usr/bin/env python3
"""Independent, read-only integrity audit of published Sätila Splits data.

Intended to run on a separate branch from active Codex frontend development.
Structural contradictions are fatal. Source-derived timing anomalies are reported
rather than silently corrected or misrepresented as invented observations.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import re
from pathlib import Path

FAMILIES = ("ultra85", "trail43", "trail22")
STATUS = ("FINISHED", "DNF", "DNS", "DSQ", "UNKNOWN")
COURSE_SHA = {
    "trail5": "304fe04cba9ae22840253a99589fe142c31971ee129cc3fb38dde0ecfbc7144d",
    "trail10": "24fc6f0ff6eca90dade4471e4743dccbed2272c02fe88b6619c46c6ece9d7c91",
    "trail22": "c78872ddd3d9e0575eb260227a2d9b40455d7841d0d8a4dcfe71614356a06c39",
    "trail43": "4b10bee2201e8f2493a1bf564c1603c5431c123fdc8d19dfb432655fb04ee827",
    "ultra85": "c5c313faf2b137cfeacf3b90cee4638094070793d70c8a88ca00944360f582c0",
}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def finite_positive(n):
    return isinstance(n, (int, float)) and not isinstance(n, bool) and math.isfinite(n) and n > 0


def explicit_class_sex(name):
    value = str(name or "").strip().casefold()
    if re.match(r"^(kvinna|kvinnor|dam)(\b|\s|$)", value):
        return "F"
    if re.match(r"^(man|män|herr)(\b|\s|$)", value):
        return "M"
    return None


def audit(root):
    failures, warnings = [], []
    details = []
    boot = read(root / "bootstrap.json")
    editions = boot.get("editions") or []
    if len(editions) != 27:
        failures.append(f"Expected 27 editions; got {len(editions)}")
    expected_years = {2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024, 2025}
    seen_keys = set()
    catalog_status = collections.Counter()
    total_results = total_splits = finished_total = 0

    for ed in editions:
        key = ed["race_key"]
        if key in seen_keys:
            failures.append(f"Duplicate edition key: {key}")
        seen_keys.add(key)
        year, family = ed["year"], ed["family"]
        if year not in expected_years or family not in FAMILIES:
            failures.append(f"Unknown race edition: {key}")
        if key != f"{year}-{family}":
            failures.append(f"Race key does not match year/family: {key}")
        file = root / "races" / f"{key}.json"
        if not file.exists():
            failures.append(f"Race file missing: {key}")
            continue
        race = read(file)
        for field in ("race_key", "family", "year", "event_id"):
            if ed.get(field) != race.get(field):
                failures.append(f"{key}: catalogue/race mismatch in {field}")
        if not str(race.get("source_url", "")).startswith("https://"):
            failures.append(f"{key}: no HTTPS official source")
        results, splits, stations = race["results"], race["splits"], race["stations"]
        result_ids = {r["id"] for r in results}
        station_ids = {s["uid"] for s in stations}
        if len(result_ids) != len(results):
            failures.append(f"{key}: duplicate result IDs")
        if len(station_ids) != len(stations):
            failures.append(f"{key}: duplicate station IDs")
        if len(stations) != ed["timing_stations"]:
            failures.append(f"{key}: station count differs from catalogue")
        finishes = [s for s in stations if s["is_finish"]]
        if len(finishes) != 1:
            failures.append(f"{key}: expected exactly one public finish station")
        finish_id = finishes[-1]["uid"] if finishes else None
        if sorted(stations, key=lambda s: (s["sort"], s.get("km") or 0, s["uid"])) != stations:
            failures.append(f"{key}: station ordering unstable")
        station_order = {s["uid"]: i for i, s in enumerate(stations)}
        observations = collections.defaultdict(list)
        seen_observation_keys = set()
        for sp in splits:
            uid, sid = sp.get("result_id"), sp.get("station_uid")
            if uid not in result_ids:
                failures.append(f"{key}: orphan split for {uid}")
            if sid not in station_ids:
                failures.append(f"{key}: unknown station {sid}")
            if (uid, sid) in seen_observation_keys:
                failures.append(f"{key}: duplicate split {uid}/{sid}")
            seen_observation_keys.add((uid, sid))
            if not finite_positive(sp.get("elapsed_seconds")):
                failures.append(f"{key}: zero/invalid public TIME split for {uid}/{sid}")
            observations[uid].append(sp)
        counter = collections.Counter(r["status"] for r in results)
        for status in counter:
            if status not in STATUS:
                failures.append(f"{key}: undocumented status {status}")
        if sum(counter.values()) != ed["results"]:
            failures.append(f"{key}: result count mismatch")
        for label, source in (("finishers", "FINISHED"), ("dnf", "DNF"), ("dns", "DNS"), ("dsq", "DSQ"), ("unknown", "UNKNOWN")):
            if counter[source] != ed[label]:
                failures.append(f"{key}: {label} catalogue mismatch: {ed[label]} vs {counter[source]}")
        if len(splits) != ed["split_observations"]:
            failures.append(f"{key}: split count mismatch")
        anomalous_monotone = finish_discrepancy = finish_without_obs = dns_observations = 0
        for r in results:
            uid = r["id"]
            class_sex = explicit_class_sex(r.get("class_name"))
            if r.get("sex") in ("F", "M") and class_sex and r["sex"] != class_sex:
                failures.append(f"{key}: explicit class/sex contradiction remains analytically classified: {uid}")
            obs = sorted(observations.get(uid, []), key=lambda sp: station_order.get(sp["station_uid"], 10**9))
            for a, b in zip(obs, obs[1:]):
                if b["elapsed_seconds"] <= a["elapsed_seconds"]:
                    anomalous_monotone += 1
            if r["status"] == "FINISHED":
                if not finite_positive(r.get("finish_seconds")):
                    failures.append(f"{key}: FINISHED has no positive finish time: {uid}")
                finish_obs = next((sp for sp in obs if sp["station_uid"] == finish_id), None)
                if not finish_obs:
                    finish_without_obs += 1
                elif abs(finish_obs["elapsed_seconds"] - r["finish_seconds"]) > 0.011:
                    finish_discrepancy += 1
            elif r.get("finish_seconds") is not None:
                failures.append(f"{key}: {r['status']} has a synthesized/incorrect finish time: {uid}")
            if r["status"] == "DNS" and obs:
                dns_observations += 1
        if finish_without_obs or finish_discrepancy:
            failures.append(f"{key}: FINISHED / public finish disagreement: missing={finish_without_obs}, mismatched={finish_discrepancy}")
        if anomalous_monotone:
            warnings.append(f"{key}: {anomalous_monotone} source time order anomalies; preserve raw, exclude invalid segment pairs")
        if dns_observations:
            warnings.append(f"{key}: {dns_observations} DNS entrants nevertheless have public TIME observation(s); preserve source flags, inspect")
        if ed.get("route_file"):
            route_path = root / ed["route_file"]
            if not route_path.is_file():
                failures.append(f"{key}: route asset missing")
            else:
                route = read(route_path)
                if route.get("type") == "OFFICIAL_ORGANIZER":
                    if year != 2025 or family not in ("trail22", "trail43"):
                        failures.append(f"{key}: organizer route reuse not authorized for edition")
                    if route.get("source_sha256") != COURSE_SHA[family]:
                        failures.append(f"{key}: official route checksum does not match source registry")
                    if route.get("edition_references") != [2025, 2026]:
                        failures.append(f"{key}: unrecorded organizer reuse references")
                elif route.get("type") == "VERIFIED_PARTICIPANT":
                    if ed.get("route_status") != "participant_track_display_only":
                        failures.append(f"{key}: participant course must remain display-only")
                    if route.get("race_key") != key or route.get("edition_references") != [year]:
                        failures.append(f"{key}: participant route borrowed across editions")
                    if route.get("source_sha256") != ed.get("route_source_sha256"):
                        failures.append(f"{key}: participant GPX digest is not linked to edition")
                else:
                    failures.append(f"{key}: unknown route provenance")
        elif year == 2025 and family in ("trail22", "trail43"):
            failures.append(f"{key}: agreed 2025/2026 organizer route is not linked")
        details.append({
            "race_key": key, "results": len(results), "statuses": dict(counter),
            "splits": len(splits), "stations": len(stations),
            "source_time_order_anomalies": anomalous_monotone,
            "source_dns_with_time": dns_observations,
            "route": ed.get("route_file"),
        })
        catalog_status.update(counter)
        total_results += len(results)
        total_splits += len(splits)
        finished_total += counter["FINISHED"]

    if {ed["year"] for ed in editions} != expected_years:
        failures.append("Historical years mismatch; 2020 must remain absent")
    for year in expected_years:
        if {ed["family"] for ed in editions if ed["year"] == year} != set(FAMILIES):
            failures.append(f"{year}: one or more core race families missing")
    if total_results != 3272:
        failures.append(f"Unexpected results total: {total_results} vs baseline 3272")

    inventory_file = root / "route-inventory.json"
    inventory = read(inventory_file) if inventory_file.exists() else []
    organizer = [route for route in inventory if route.get("type") == "OFFICIAL_ORGANIZER"]
    participants = [route for route in inventory if route.get("type") == "VERIFIED_PARTICIPANT"]
    if len(organizer) != 5 or {route["family"] for route in organizer} != set(COURSE_SHA):
        failures.append("Five checksum-locked organizer sources must remain present")
    if len(organizer) + len(participants) != len(inventory):
        failures.append("Unexpected unclassified route provenance")
    for route in organizer:
        family = route["family"]
        if route.get("source_sha256") != COURSE_SHA.get(family):
            failures.append(f"{family}: official source checksum changed")
        expected_editions = [2026] if family == "ultra85" else [2025, 2026]
        if route.get("edition_references") != expected_editions:
            failures.append(f"{family}: organizer reuse status mismatch")
    for route in participants:
        key = route.get("race_key")
        edition = next((ed for ed in editions if ed["race_key"] == key), None)
        if not edition or route.get("edition_references") != [edition["year"]]:
            failures.append(f"{key}: participant GPX not restricted to exact edition")
        elif edition.get("route_source_sha256") != route.get("source_sha256"):
            failures.append(f"{key}: participant route source SHA mismatch")
    for route in inventory:
        if not finite_positive(route.get("geometry_length_km")):
            failures.append(f"{route.get('race_key', route.get('family'))}: invalid display geometry length")

    report = {
        "schema": "satila-source-audit-v1", "subject": "current static published bundles",
        "scope": "9 historical years; all three primary race families; five organizer GPX",
        "summary": {
            "editions": len(details), "results": total_results,
            "splits": total_splits, "finishers": finished_total,
            "statuses": dict(catalog_status),
            "organizer_routes": len(organizer),
            "participant_display_routes": len(participants),
            "failures": len(failures), "warnings": len(warnings),
        },
        "failures": failures, "warnings": warnings, "editions": details,
        "method": "Comparisons against immutable catalogue and public observations. No source timing values, route geometries or athlete records are altered.",
    }
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=str(Path(__file__).resolve().parents[1] / "docs" / "data"))
    parser.add_argument("--output", help="Optional JSON report filename")
    args = parser.parse_args()
    report = audit(Path(args.data))
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))
    for warning in report["warnings"]:
        print("SOURCE WARNING:", warning)
    for failure in report["failures"]:
        print("INTEGRITY FAILURE:", failure)
    raise SystemExit(1 if report["failures"] else 0)


if __name__ == "__main__":
    main()
