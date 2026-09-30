# AGENTS.md – Sätila Splits

## Project state
This repository is in the source-discovery and data-foundation phase for Sätila Trail Run. Do not start by cloning a frontend wholesale. Establish verified results, checkpoints, GPX provenance and course versions first.

## Scope
Primary race families:
- `ultra85` — including historical 80/82 km variants
- `trail43` — including historical ~42 km variants
- `trail22` — including historical ~21 km variants

Initial working window: 2021–2026. Historical research may extend to 2016.

## Source-of-truth rules
- Official timing data is primary for results when available.
- Preserve raw source payloads before normalization.
- Never fabricate splits, checkpoints, ranks, DNS/DNF status or course geometry.
- Third-party race databases are cross-check sources unless they are the original homologation source.
- A listed aid station or cutoff does not prove that an official timing split exists there.

## Course rules
- Marketing distance labels are not proof of identical geometry.
- Treat every year/distance as a separate course candidate until geometry comparison proves equivalence.
- Canonical checkpoint identity is geographic/name based, not fixed-kilometer based.
- Store the actual chainage of a checkpoint separately for each event/course version.
- Preserve both planned course and race-day course when evidence shows a difference.
- A participant GPX is evidence of the route actually run, not automatically proof of the official intended route.

## GPX provenance
Use an explicit source class:
- `OFFICIAL_ORGANIZER`
- `ITRA_TRACE`
- `RACE_TRACKER`
- `VERIFIED_PARTICIPANT`
- `RECONSTRUCTED`

Every retained asset should record source URL/reference, year, race family, verification status, intended filename, checksum and notes.

## Result import
EQ Timing event IDs and other known event identifiers belong in `config/source-registry.json`.
Do not scrape presentation HTML when a structured export/API/source payload is available.

## Engine strategy
Sätila Splits should reuse the generic analysis concepts already proven in Gotaleden and Österlen:
- source-driven capabilities
- course-version awareness
- explicit provenance
- raw/normalized separation
- reproducible validation

Do not introduce Sätila-specific frontend logic until the generic contract can no longer express a verified requirement.
