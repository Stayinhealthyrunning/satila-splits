# Sätila → Loppanalys Comparison 2.0 migration plan

## Implementation status 2026-10-07

Implemented on `codex/comparison-2-satila` for draft review. Direct Comparison now uses the canonical B-minus-A sign, nine duel KPIs, official placement journey, exact segment duel, edition-field normalization, capability-driven sparse rendering, synchronized two-runner course playback, 30/60/120/180-second duration choices, follow-both default camera, 30% persisted audio and shareable URL state.

`cross_edition_comparison` and `team_entity` remain false. Sätila's physical-pace gate is intentionally stricter than the generic reference: gated segments use exact segment-time normalization with explicit copy and never manufacture min/km.

## Goal

Bring Sätila's Direct Comparison into semantic and interaction parity with the
Ultravasan Comparison 2.0 reference **without replacing Sätila-specific evidence
rules or its existing strong map/elevation interaction**.

The canonical contract is:

- `Stayinhealthyrunning/ultravasan-analys/config/comparison-contract-v2.json`
- explanatory reference: `reports/COMPARISON_2_0.md` in the Ultravasan repo.

This plan is deliberately repo-local so an implementation agent can work from
Sätila's actual architecture instead of copying Ultravasan files.

## Current strengths to preserve

Sätila already has several pieces that must survive the migration:

- exact two-result Direct Comparison inside a dialog;
- observed checkpoint gap chart with axes;
- real passage/segment table;
- shared-race-clock two-runner map and elevation interaction;
- route/elevation seeking;
- a separate 2–5 participant Kartduell with soundtrack;
- strict physical-pace gating when timing-distance metadata is not trustworthy;
- no fictional times in public tables.

These are assets, not technical debt.

## Gaps against Comparison 2.0

### 1. Analytical summary

Current Direct Comparison uses a short free-form insight list. Replace/augment it
with the common KPI contract:

- final verified difference;
- official passages led by A / B / equal;
- observed lead changes;
- A most time gained;
- B most time gained;
- nearest observed checkpoint;
- largest observed checkpoint gap.

The UI should use the same concepts/order as the reference implementation.

### 2. Signed-gap semantics

Current code uses `A elapsed - B elapsed` in parts of the UI, where positive
means B is ahead. Comparison 2.0 defines:

`B elapsed - A elapsed`

Positive therefore means **A ahead**.

Normalize the analysis model and labels so the same sign convention is used
across Loppanalys.

### 3. Official placement journey

Sätila currently exposes placement values in the passage table but lacks the
standard two-line official placement journey. Add it only where both runners
have source-supported placement observations. Missing observations must break
the series.

### 4. Field-relative performance

Add the Comparison 2.0 field-normalization panel with an explicit 0% reference.

For segments with trustworthy physical distance, use the normal pace-relative
measure. Where Sätila's existing distance capability rejects physical pace,
**do not force min/km**. The adapter may instead normalize exact segment time
against the edition's stable exact-segment median, with the UI saying that the
metric is segment-time-relative rather than pace-relative.

Reference cohort must be stable and disclosed, with n >= 5.

### 5. Playback alignment

Preserve Sätila's existing interactive implementation but align the controls:

- 30 s / 1 min / 2 min / 3 min choices;
- 2 min default;
- 30% neutral audio volume;
- persisted audio on/off and volume;
- default camera: follow both;
- whole course and follow leader alternatives where geometry supports them;
- smooth playback and synchronized race clock, map and elevation.

Direct Comparison should use the soundtrack too, not only Kartduell.

### 6. Shareable state

Add a shareable Direct Comparison URL that contains the two selected result IDs
and supported state such as current race clock/selected segment when practical.
Opening the URL must restore a valid comparison without changing source data.

## Sparse-data behavior

Sätila should adopt the shared sparse fallback as a capability even though most
useful 43/85 km editions have richer timing. If an edition has too little
official timing for the full journey, render only the real anchors rather than
constructing extra analytical checkpoints.

## Explicit non-goals

- Do not add cross-edition Direct Comparison yet.
- Do not make 22 km appear to have route/split coverage it does not have.
- Do not weaken current timing-distance plausibility checks.
- Do not copy Ultravasan DOM/CSS wholesale.
- Do not change result/status counts or source files.

## Suggested implementation order

1. Introduce a small comparison view-model matching the common capability names.
2. Normalize signed-gap/KPI semantics.
3. Add placement journey.
4. Add field-relative panel with Sätila distance fallback.
5. Align replay/audio controls while preserving current map/elevation engine.
6. Add share state.
7. Add sparse fallback.
8. Run source, unit, responsive and browser regression.

## Acceptance examples

A same-edition Trail43 comparison with full evidence should expose the full
Comparison 2.0 flow. A segment whose physical distance is rejected may still
show exact segment time and time-relative field context but must not show a
fabricated pace. An edition without adequate intermediate timing should remain
useful through sparse mode rather than fake a full chart.
