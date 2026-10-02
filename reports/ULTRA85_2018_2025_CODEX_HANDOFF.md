# Ultra85 history handoff — 2026-10-02

Target branch: `integration/ultra85-history-2018-2025`; base is `main` as of handoff.

## Owner-provided release package (download from ChatGPT and extract at repository root)

`satila-ultra85-route-release-2026-10-02.zip`
SHA-256: `052116297b943d3672644d44390607d6c1beade1c8186b0e0b8c885703d4d88f` (101456 bytes, tested ZIP).
Contains seven sanitized, year-specific participant course JSONs in `docs/data/routes/`, plus two QA reports in `reports/`. Original participant GPX are stored in the owner's private ChatGPT Library, not in this package; DO NOT publish raw originals, names or timestamps.

Required seven source SHA-256s and output display lengths:
- 2018: `5f0864fba534b23d48ac2adde73240bd58d48946d4a2cb092757a9b4304175ec`, 84.147947 km
- 2019: `4b508c9071480feea7823ca8df371cf39030b74d62370851df8de485fbce9510`, 81.151690 km
- 2021: `13c033f0e4a336334f9030ea322f4df3df226415c850896fd511e980e36ed294`, 82.775276 km
- 2022: `0b6cd4a39ecce9fe6262f03b8c9be15c59c6428277c0b67497402d95d95207b0`, 84.210529 km
- 2023: `e363954507767a4a06f74f4547d4e5b7216849452317f4359c368ecd28636e81`, 81.048957 km
- 2024: `042ddbb7d32862fbcc415f284577f3dad8225adec47f1240e9dd9caa7f7f18c6`, 83.364334 km
- 2025: `d54db03d752dd1e6679492f595aa6121c4396d94ed13c9903f5a974b11380d47`, 81.413504 km

The display lengths differ slightly from original (unsimplified) polyline lengths, intentionally. No elevation samples exist in these RouteGadget tracks: per-point altitude is null.

## Codex integration contract
For each race_key `<year>-ultra85` in `docs/data/bootstrap.json`, set:
- `route_status = "participant_track_display_only"`
- `route_file = "routes/<year>-ultra85-participant.json"`
- `route_source_sha256` equal to that year's JSON `source_sha256`
- `measured_route_geometry_km` equal to JSON `geometry_length_km`
- `course_version = "<year>-ultra85-participant-display-not-canonical"`

Keep 2026 organizer route distinct and unchanged; don't reuse it for any historical edition. Keep 43km/22km assignments and EQ Timing observations unchanged. Display route independently of partial or absent TIME observations; never derive official timing from GPX. Handle null altitude gracefully: display no elevation graph or explanatory missing-data state, not invented 0 m elevation. Each year uses its *own* JSON, no inferred equivalence.

Review `reports/ULTRA85_GEOMETRY_COMPARISON.json` and `reports/ULTRA85_SOURCE_SUMMARY.json`; avoid equating participant GPS length with certified organizer course length. Add automated browser/data regression tests (2018, 2019, 2021–2025) for route load, line rendering, null elevation, source provenance, no participant identity/timestamps, replay with partial timing, and no year leakage. Run project acceptance/CI; open PR against main, merge/publish only when green and ownership approvals satisfied.
