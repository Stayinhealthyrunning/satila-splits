# AGENTS.md – Sätila Splits / 2026-10-01 post-integration

## Current stage: do not restart source discovery

The original AGENTS.md previously described the source-discovery phase. That is historical. The first complete source foundation and an integrated release-review candidate now exist.

- Continue from origin/integration/codex-independent-qa-2026-10-01, Draft PR #7. Not from main or the older first-draft build.
- First read reports/PRE_CODEX_FINAL_HANDOFF_2026-10-01.md, current BUILD_STATE.json, reports/SAETILA_SPLITS_BUILD_BLUEPRINT_2026-10-01.md, and latest GitHub Actions result for the actual current code SHA.
- reports/CODEX_PARITY_AUDIT.md refers to an older Codex checkpoint; K04 Replay, K05 map duel and T09 pagination have since been implemented. Do not rebuild them.
- Preserve original Codex branch codex/saetila-complete-first-draft at a71a5ef and owner's C:\Git\satila-splits\reports\qa-local. No reset --hard, clean -fd, checkout -f, force push, overwrite or reclone.
- For work after quota reset, inspect git status, existing worktrees and branches; create a NEW dedicated Git worktree based on the latest origin/integration/codex-independent-qa-2026-10-01, then a Draft PR back to that integration branch. No automatic merge to main or publication.

## Fixed verified source contract

- Nine EQ Timing result years: 2016–2019 and 2021–2025; three main families (ultra85/trail43/trail22) each year. 27 RaceEdition, 3,272 result rows, 2,649 FINISHED, 128 DNF, 494 DNS, 1 UNKNOWN, 16,525 actual public TIME observations. 2020 is an archive gap, not a zero-participant result. There are no invented 2026 race results.
- Public curated assets: docs/data/bootstrap.json, docs/data/races/*.json, docs/data/coverage.json, docs/data/source-fingerprints.json, docs/data/routes/*.json. All original raw EQ Timing and participant GPX data remain private, never under docs/, public Git history, public release or review package.
- Five organizer GPX files are SHA-locked; 21/43 km 2025/26 reuse is an explicitly documented assumption. The 85 km 2026 organizer route is a separate prospective version and must not be borrowed for 2025. Never infer old CourseVersion equivalence from unchanged race label.
- 2025 trail43 Tostared is metadata-only (zero TIME). Real Grind→Torrås is one 15.0 timing-km observed segment with n=130; seven effective segments. Preserve Tostared in station/field metadata, exclude it from observed passage-coverage curves to avoid a false zero dip.
- 2023 trail43 has two n=8 segments (F=4, M=4), so pooled median but no quartiles or sex medians. 2016 ultra85 has only two female FINISHED, never show bronze or female median.
- 2023/24 trail43 Torrås→Almered: real TIME/n valid, physical timing-distance pace/min/km not verified. The official timing-axis and GPX route-display-distance are separate.
- Currently all 128 DNF have no linked public TIME passage in published bundles. DNF count is valid, but last checkpoint/exit is UNKNOWN. DNS is excluded from known starters, UNKNOWN status remains separate.
- Median requires n>=5; quartiles n>=10; deciles n>=20; group/sex median n>=5 in that subset. No manufactured splits, ranks, age, person matches across years, or runner photos from social media.
- Preserve source registry and exact chainage per edition. A participant GPX is evidence of the path run, not automatically official intended race geometry.

## Implementation already done; regress rather than rebuild

- Profiles, result filters, podiums, source-gated segment stats, individual split-based goal plan, linked official-route SVG map/elevation, history, status/coverage, age/class/club analytics, D16 pacingindex.
- K04 timed personal Replay and K05 2–5-runner map duel with shared clock, leaderboard and two-way map/elevation scrub.
- D11 last actual positive segment strength, D18 class selector, D19 synchronized heatmap, D22 segment-linked Course Intelligence, T07 route publication/reservation. DNF unknown, metadata-only Tostared, and source-aware pace/quantile gating.
- Hero copy, mobile Escape/ARIA, Back/Forward deep links, dialog focus, missing-edition error and public privacy controls are already corrected.
- Original official runner/hero visual assets are locked. Do not substitute or scrape athlete photographs.

## Next Codex pass after 16:13

1. Review real desktop/mobile screenshots at 1440/900/768/390 against docs/assets/design-reference.webp and approved Hero. Confirm long tables on mobile and remove only actual visual/interaction defects.
2. Finish genuinely remaining blueprint UX, such as D07 scatter zoom/reset, T01 sort/keyboard and remaining D21/K03 selected-segment interactions. The new D11/D18/D19/D22/T07 functions are already implemented and tested.
3. K01/D23 physical checkpoint anchors, tiles and T06 segment D+/D- depend on accepted source geometry/anchor evidence. K02 historic dual-route overlay, D25 joined interyear performance and D26 comparable records remain evidence-gated. Do not invent physical anchors or borrow courses to force completion.
4. Run the entire regression on each final candidate: python tools/run_release_candidate_checks.py --all. The integrated CI workflow is .github/workflows/integration-candidate.yml. Require source-and-method, browser-core, release-gates and dependent review-package GREEN on exactly the final code SHA. Verify no source/provenance drift.
5. Generate new screenshot and static review ZIP on that same SHA, then wait for project owner visual approval. Never auto-merge to main or publish to Loppanalys.se.

Private raw archive artifact 11142571759 expires 2026-10-31. Owner secure backup guidance: issue #6, preferably complete by October 25.
