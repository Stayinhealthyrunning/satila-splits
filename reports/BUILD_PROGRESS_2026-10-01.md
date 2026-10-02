# Sätila Splits – build checkpoint 2026-10-01

## Durable state

Branch: `build/full-first-draft-2026-10-01`

Completed and committed:
- S0 build/provenance foundation and resumable `BUILD_STATE.json`
- EQ Timing raw artifact identified and downloaded locally from workflow run `36818159977`, artifact `11142571759`
- official organizer GPX checksums registered for 5/10/21/43/85 km
- 2025→2026 organizer route-reuse decision recorded for 5/10/21/43 km
- reproducible conservative EQ Timing normalizer / route exporter committed as `tools/build_satila.py`
- first-draft page shell committed as `docs/index.html`

## Verified local first draft

The recovered local build is not hypothetical. It has been executed against the downloaded full EQ Timing archive and contains:
- 27 RaceEdition bundles across 2016–2019 and 2021–2025
- 3,272 race-result appearances in the three main families
- official TIME observations only for splits
- 2025 organizer route assets for 21/43 km under the approved 2025–2026 reuse assumption
- no route borrowing for older editions without evidence

Browser QA passed at:
- 1440×900
- 900×900
- 390×844

Assertions passed:
- all three families load
- 2016 and 2025 load
- result tables and segment tables render
- sex-separated podiums render with initial avatars
- runner profile opens and produces data-backed insights
- 2025 21/43 km route gating works; older unverified routes remain unavailable
- no JavaScript page errors
- no missing fixture requests
- no horizontal document overflow

Live local HTTP QA additionally passed:
- full hero asset loads
- 27-edition history table
- 43 km interactive course
- 10-hour personal race plan
- two real runners selected for head-to-head
- map and elevation profile both scrub the same duel position
- zero HTTP/JavaScript errors

## Resume point

Continue with small commits only:

1. Commit `docs/assets/style.css`, then verify blob/file hash.
2. Commit `docs/assets/app.js`, then verify syntax/hash.
3. Commit approved `docs/assets/hero.webp` and design reference.
4. Commit bootstrap + route assets + 2025 race bundles first; open a reviewable Pages build.
5. Add historical race bundles in year batches.
6. Commit browser smoke/live E2E tests.
7. Run CI and only then advance `BUILD_STATE.json`.

Do not restart GPX research or re-fetch EQ Timing unless source fingerprints change.
