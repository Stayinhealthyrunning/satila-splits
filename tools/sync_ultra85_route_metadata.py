#!/usr/bin/env python3
"""Synchronize accepted year-locked Ultra85 display-route metadata.

The bootstrap catalogue is the reviewed route assignment. This migration copies
only that route metadata into the matching race and coverage records. Official
results, public TIME observations, stations, and participant-route geometry are
read-only and are fingerprinted before and after the update.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data"
YEARS = (2018, 2019, 2021, 2022, 2023, 2024, 2025)
DISTANCE_NOTE = (
    "EQ Timing registers 82 km; the organizer invitation advertises the race as "
    "85 km. A year-specific participant track provides display geometry only and "
    "does not resolve the official race distance."
)
RACE_FIELDS = (
    "course_version",
    "route_status",
    "route_file",
    "route_source_sha256",
    "measured_route_geometry_km",
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def fingerprint(value) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main() -> None:
    bootstrap = load(DATA / "bootstrap.json")
    editions = {edition["race_key"]: edition for edition in bootstrap["editions"]}
    coverage_path = DATA / "coverage.json"
    coverage = load(coverage_path)
    coverage_by_key = {row["race_key"]: row for row in coverage}
    inventory = load(DATA / "route-inventory.json")
    inventory_by_key = {row.get("race_key"): row for row in inventory}

    for year in YEARS:
        key = f"{year}-ultra85"
        edition = editions[key]
        if year in (2019, 2021):
            edition["distance_evidence_note"] = DISTANCE_NOTE
        inventory_row = inventory_by_key[key]
        route = load(DATA / edition["route_file"])
        race_path = DATA / "races" / f"{key}.json"
        race = load(race_path)

        assert edition["route_status"] == "participant_track_display_only"
        assert edition["route_file"] == f"routes/{key}-participant.json"
        assert route["type"] == "VERIFIED_PARTICIPANT"
        assert route["race_key"] == key and route["edition_references"] == [year]
        assert route["source_sha256"] == edition["route_source_sha256"]
        assert route["geometry_length_km"] == edition["measured_route_geometry_km"]
        assert inventory_row["source_sha256"] == route["source_sha256"]

        official_before = fingerprint(
            {name: race[name] for name in ("stations", "results", "splits")}
        )
        for field in RACE_FIELDS:
            race[field] = edition[field]
        if year in (2019, 2021):
            race["distance_evidence_note"] = DISTANCE_NOTE
        assert official_before == fingerprint(
            {name: race[name] for name in ("stations", "results", "splits")}
        )
        write(race_path, race)

        coverage_row = coverage_by_key[key]
        if year in (2019, 2021):
            coverage_row["distance_evidence_note"] = DISTANCE_NOTE
        coverage_row.update(
            {
                "course_version": edition["course_version"],
                "route_status": edition["route_status"],
                "route_file": edition["route_file"],
                "route_source_type": route["type"],
                "route_source_filename": inventory_row.get("source_filename"),
                "route_sha256": route["source_sha256"],
                "route_geometry_km": route["geometry_length_km"],
                "route_evidence_note": inventory_row["evidence_note"],
                "route_source_sha256": route["source_sha256"],
                "measured_route_geometry_km": route["geometry_length_km"],
            }
        )
        print(f"SYNCED {key}: {route['geometry_length_km']:.3f} km display route; official TIME unchanged")

    write(DATA / "bootstrap.json", bootstrap)
    write(coverage_path, coverage)


if __name__ == "__main__":
    main()
