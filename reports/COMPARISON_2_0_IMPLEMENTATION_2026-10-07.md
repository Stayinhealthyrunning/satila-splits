# Sätila Comparison 2.0 — implementation and review record

## Scope

This change migrates the existing same-edition, exactly-two-result Direct Comparison to the shared Loppanalys Comparison 2.0 semantics. It extends Sätila's existing map/elevation engine; it does not copy the Ultravasan DOM/runtime and does not change public race, split or route data.

## Implemented capabilities

- `finish_comparison`
- `checkpoint_gap` with `gap = B elapsed - A elapsed`
- `placement_journey` from published checkpoint places only
- `segment_comparison` from exact adjacent observations
- `edition_field_normalization`, n≥5
- `shared_course_context`
- `animated_two_result_comparison`
- `elevation_seek`
- `shareable_comparison_state`
- `sparse_comparison_fallback`
- `audio`

Intentionally false: `cross_edition_comparison` and `team_entity`.

## Sätila-specific evidence rules retained

- Physical pace remains hidden when timing distance is not verified. The 2023/2024 Trail43 Torrås→Almered case still shows exact segment time and may use exact segment-time normalization, but never min/km.
- Metadata-only Tostared and the rejected non-official Grind observations do not become analytical anchors.
- No DNF exit point, missing split, checkpoint place or route geometry is fabricated.
- Route provenance, historical 22 km limits and 82/85 km ambiguity remain unchanged.
- A/B colors describe comparison roles and do not replace the pink/blue sex-analysis palette.

## Interaction contract

The modal follows participant context → KPI strip → observed gap → official placement → segment duel → field normalization → synchronized course → method. Segment/checkpoint clicks synchronize the course state where route capability exists. Playback offers 30/60/120/180 seconds, defaults to 120 seconds, defaults to follow both, and uses the shared persisted soundtrack preference at a neutral 30% initial volume. Closing the dialog stops and rewinds audio.

The URL hash preserves family, year, result A, result B and, when present, race-clock and selected-segment state. Restoration validates both result IDs against the selected RaceEdition and never writes source data.

## QA evidence

- `python tools/run_release_candidate_checks.py --source`: PASS on 2026-10-07. Machine result: `reports/comparison-v2-source-qa.json`.
- Rich 2025 Trail43 Direct Comparison: browser-tested at 1440×900, 900×900, 768×900 and 390×844 with no horizontal overflow.
- 2023 Trail43 Torrås→Almered: browser-tested exact-time comparison with pace hidden and segment-time field normalization.
- Sparse 2018 Trail22 pair: browser-tested simplified real-anchor journey without borrowed route.
- Map Duel 2–5 and individual Replay remain in the full release browser regression.

Final browser/all-command results and exact head SHA are recorded after the candidate commit. The draft PR must not be merged or published automatically.
