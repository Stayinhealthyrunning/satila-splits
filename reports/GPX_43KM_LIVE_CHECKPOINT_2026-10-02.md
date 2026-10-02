# 43 km 2021–2025 — LIVE and verified (2026-10-02)

## Owner source import
- Original owner-supplied 2021–2025 GPX were restored and checksum-verified.
- Durable ZIP: `data/source-archive/satila-43km-source-and-normalized-2021-2025.zip`.
- Separate original GPX and two deterministic reconstructed normalized GPX/JSON are in `data/participant-gpx/` and `data/normalized-gpx/` (not in publishable `docs/`).
- Import Actions **37002453066** SUCCESS, generated main commit `5f8f28712b03ddd959787ae4fd6208b34c2039ca`, `RELEASE CANDIDATE QA PASS`.
- New normalized output is not claimed to be byte-identical to the missing September export.

## Historical 43km routes connected to website
| Year | Display route | Points | Provenance |
|---|---|---:|---|
| 2021 | routes/2021-trail43-participant.json | 1090 | Owner-accepted normalized participant corridor 2021–22, 44.30917km |
| 2022 | routes/2022-trail43-participant.json | 1090 | Same accepted corrected source, year-locked edition asset |
| 2023 | routes/2023-trail43-participant.json | 822 | Owner-accepted normalized participant consensus 2023–25, 41.873734km |
| 2024 | routes/2024-trail43-participant.json | 1018 | Already separately verified exact-year owner GPX |
| 2025 | routes/trail43-2025-2026.json | 1380 | Organizer geometry with documented 2025–26 reuse assumption |

All GPX display routes are separate from the nominal official EQ Timing distance axis. The normalized participant courses have explicit `NORMALISERAD DELTAGARBANA` map labels; only genuine monotone published TIME endpoints may generate observed split statistics. Map availability no longer depends on all checkpoint timings being present.

## QA, merge and deployment
- PR **#20** merged, commit `9d479ad237ef7db1302bca42db80d3fcf18461c6`.
- Restored source/geometries and independent browser QA: Actions **37002782900 SUCCESS**. All 2021–2025 year-scoped maps and elevation views passed Chromium at both **1440px and 390px**, plus independent 2024 partial-checkpoint browser test. Complete `--source` regression PASS.
- Historical participant route and partial TIME QA: **37002782901 SUCCESS**.
- Soundtrack regression, JS and browser smoke: **37002783017 SUCCESS**.
- Latest standalone Pages deployment: **37003005514 SUCCESS** with `pages_build_version=9d479ad237ef7db1302bca42db80d3fcf18461c6`. Reported environment URL: `http://www.loppanalys.se/satila-splits/` (review canonical HTTPS URL `https://www.loppanalys.se/satila-splits/`).
- Portal Draft PR #8 remains separate and unmerged pending owner review.
- Issue #17 remains open for other distance/year GPX source leads; the 43km 2021–25 portion is completed.

## Crash-resilient restart
Do not redo 43km normalization or ask owner to re-upload 2021–25 GPX. This checkpoint and content-addressed GitHub original and derived files are durable.
