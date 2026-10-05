# AGENTS.md – Sätila Splits

## Current authoritative state

Use **current `main`** as the starting point. The old 2026-10-01 build/integration branches and their Draft PR instructions are historical and must not be used as the active handoff.

As of 2026-10-05:

- the standalone site is deployed from `docs/` through GitHub Pages,
- historical Ultra85 display routes for 2018, 2019 and 2021–2025 are integrated,
- 43 km route coverage for 2021–2025 is integrated,
- the non-official Grind checkpoint is excluded from published analysis,
- Torrås semantics for 2023–2025 are corrected,
- sex palette/axis-density changes are integrated,
- privacy/identity suppression is integrated,
- the individual runner analysis has been rebuilt from the Gotaleden profile architecture,
- there are no open pull requests after repository cleanup.

Before changing code, inspect current `main`, current open PRs, and the latest Actions result for the exact candidate SHA. Do not trust an old report or hard-coded SHA over the repository state.

## Source contract

- Nine EQ Timing result years: 2016–2019 and 2021–2025.
- Three main families: `ultra85`, `trail43`, `trail22`.
- 27 RaceEdition and 3,272 result rows.
- 2,649 FINISHED, 128 DNF, 494 DNS, 1 UNKNOWN.
- The current public analytical bundles contain **14,466 source-supported TIME observations** after exclusion of the rejected non-official Grind observations.
- Public curated assets live under `docs/data/`.
- Raw EQ Timing dumps and original participant GPX must never be added to public `docs/`, public release artifacts, or otherwise exposed unintentionally.
- Participant-derived route geometry is display/provenance evidence, not automatically an official intended race course.
- Organizer 21/43 km 2025/2026 reuse remains an explicit project assumption.
- Ultra85 2026 geometry does not validate older Ultra85 editions.
- 2023/2024 trail43 Torrås→Almered supports TIME/n but not a trustworthy physical min/km value.
- Do not invent missing passage times, ranks, checkpoints, ages, identities, course equivalence, DNF exit locations, or route elevation.

Statistical minimums remain source-aware: median n≥5, quartiles n≥10, deciles n≥20, and group/sex medians n≥5 in the relevant subset.

## Implementation state

The main frontend already contains:

- overview, results, historical trends and segment analyses,
- source-aware sex breakdowns and the approved blue/pink palette,
- individual runner profile with Gotaleden-style summary, Replay, gap/placement journey, relative speed and split table,
- shared-clock two-runner comparison and map duel,
- route/elevation interaction with source gating,
- personal target-time planning,
- privacy/identity suppression,
- responsive/mobile behavior and accessibility regression coverage.

Regress existing behavior before rebuilding it. Historical reports under `reports/` are evidence/checkpoints; they are not automatically current implementation instructions.

## Working method

For a new change:

1. Start from current `main`.
2. Keep data/provenance changes separate from purely visual changes where practical.
3. Run `python tools/run_release_candidate_checks.py --source` after source/data changes.
4. Run the relevant browser acceptance tests for UI/interactivity; for a release candidate use `python tools/run_release_candidate_checks.py --all`.
5. For a PR, require the relevant current pull-request workflows to be green on the exact head SHA.
6. Merge/publish only when the project owner has requested it and the candidate is green. Standalone Pages deploys from `main`; changes to the separate Loppanalys portal require a separate explicit task.

Do not resurrect completed first-draft workflows or obsolete integration branches just to reproduce an old process. The active workflow set on `main` is intentionally smaller after housekeeping.

## Historical references

Useful historical documentation remains in:

- `reports/SAETILA_SPLITS_BUILD_BLUEPRINT_2026-10-01.md`
- `reports/CODEX_PARITY_AUDIT.md`
- `reports/PRE_CODEX_FINAL_HANDOFF_2026-10-01.md`
- `reports/FINAL_INTEGRATION_HANDOFF_2026-10-01.md`
- `reports/QA_EVIDENCE_INDEX_2026-10-01.md`

Treat their old branch names, workflow names and release SHAs as historical evidence only.
