# Sätila Splits – första granskningsbara utkastet (2026-10-01)

## Status
**REVIEW READY — not yet approved for merge/publication on Loppanalys.se.**
Build branch: `build/full-first-draft-2026-10-01`. Reusable source and results are in GitHub; no unfinished background process is needed to open the committed static site.

## Delivered and independently checked
- Three main race families: 85 km, 43 km, 22 km.
- Nine official EQ Timing archive years (2016–2019, 2021–2025), 27 RaceEditions.
- 3,272 unique result appearances, 2,649 FINISHED, 16,525 actual TIME station observations.
- Official source status, age/class/sex only where provided by EQ; missing splits are not fabricated.
- Organizer GPX data exports for 5/10/21/43/85 km; as agreed, the internally 2025-labelled organizer 21/43 km routes are reused for 2025/2026; 85/2026 stays a separate future-course asset.
- The approved forest-green Hero and design reference; no third-party runner photos.
- Interactive results, filters, historic participation view, women/men podiums, segmentation, runner profile with individual insights, personal split-based goal plan, and two-runner head-to-head.
- Linked interactive course map and elevation profile only on a route-enabled edition; linked head-to-head map/elevation scrub by click and keyboard.
- Explicit no-borrowed-route fallback for historical editions without source-verified course geometry.
- Compact, static hosting output under `docs/`, suitable for GitHub Pages or Loppanalys integration after approval.

## Checks (independent)
- Source normalization GitHub Action successful: [36835282859](https://github.com/Stayinhealthyrunning/satila-splits/actions/runs/36835282859), all 27 editions, all 3,272 results, checksum-verified organizer GPX package.
- Independent browser regression GitHub Action successful: [36835443117](https://github.com/Stayinhealthyrunning/satila-splits/actions/runs/36835443117) on the restored production app, and [36835483334](https://github.com/Stayinhealthyrunning/satila-splits/actions/runs/36835483334) after final CI hardening.
- Desktop/tablet/mobile Chromium at 1440×900, 900×900 and 390×844: all race families, 2016/2025, profile, course feature gating, no page exceptions and no document overflow.
- Local release invariants: four tests green (27/3272/2649/16525, unique result IDs, positive observed splits, course/source gating, no external runner photographs).
- Local deep interaction test green: 2025 43 km GPX, individual profile, a goal plan totaling exactly 10:00:00, two real runners in comparison and clicks on both elevation and map move the same scrub position without JavaScript/fixture errors.

## Extended S5–S9 analytics – QA checkpoint

The extended first-draft analytics module has now been integrated into the same application runtime. It adds age/class and club analysis, sex-specific completion rates, a target-time/placing explorer, finishing progression, checkpoint spread, placement gains, a fuller segment laboratory (Q10–Q90, retention, group/sex splits, heatmap), route-aware course context and richer historical/provenance views. All views use source-gated observations; unsupported evidence is labelled.

- [Extended Chromium regression 36838917833 — PASS](https://github.com/Stayinhealthyrunning/satila-splits/actions/runs/36838917833), checked commit `c7a98d4a946590691131b523bf0e8a2503833c24`.
- GitHub CI stdout: `PASS browser 1440 900 overflow 0`, `PASS browser 900 900 overflow 0`, `PASS browser 390 844 overflow 0`, `PASS 27 real editions and 3272 result appearances`.
- The independent test now checks extension panels, the target-time interaction and repeated sex filtering before mobile document-overflow assertions.
- Fixed after initial extension integration: the historical fingerprint is scrolled *inside* its card on narrow screens; the history-year multi-selector retains the `$` query-all helper rather than `# Sätila Splits – första granskningsbara utkastet (2026-10-01)

## Status
**REVIEW READY — not yet approved for merge/publication on Loppanalys.se.**
Build branch: `build/full-first-draft-2026-10-01`. Reusable source and results are in GitHub; no unfinished background process is needed to open the committed static site.

## Delivered and independently checked
- Three main race families: 85 km, 43 km, 22 km.
- Nine official EQ Timing archive years (2016–2019, 2021–2025), 27 RaceEditions.
- 3,272 unique result appearances, 2,649 FINISHED, 16,525 actual TIME station observations.
- Official source status, age/class/sex only where provided by EQ; missing splits are not fabricated.
- Organizer GPX data exports for 5/10/21/43/85 km; as agreed, the internally 2025-labelled organizer 21/43 km routes are reused for 2025/2026; 85/2026 stays a separate future-course asset.
- The approved forest-green Hero and design reference; no third-party runner photos.
- Interactive results, filters, historic participation view, women/men podiums, segmentation, runner profile with individual insights, personal split-based goal plan, and two-runner head-to-head.
- Linked interactive course map and elevation profile only on a route-enabled edition; linked head-to-head map/elevation scrub by click and keyboard.
- Explicit no-borrowed-route fallback for historical editions without source-verified course geometry.
- Compact, static hosting output under `docs/`, suitable for GitHub Pages or Loppanalys integration after approval.

## Checks (independent)
- Source normalization GitHub Action successful: [36835282859](https://github.com/Stayinhealthyrunning/satila-splits/actions/runs/36835282859), all 27 editions, all 3,272 results, checksum-verified organizer GPX package.
- Independent browser regression GitHub Action successful: [36835443117](https://github.com/Stayinhealthyrunning/satila-splits/actions/runs/36835443117) on the restored production app, and [36835483334](https://github.com/Stayinhealthyrunning/satila-splits/actions/runs/36835483334) after final CI hardening.
- Desktop/tablet/mobile Chromium at 1440×900, 900×900 and 390×844: all race families, 2016/2025, profile, course feature gating, no page exceptions and no document overflow.
- Local release invariants: four tests green (27/3272/2649/16525, unique result IDs, positive observed splits, course/source gating, no external runner photographs).
- Local deep interaction test green: 2025 43 km GPX, individual profile, a goal plan totaling exactly 10:00:00, two real runners in comparison and clicks on both elevation and map move the same scrub position without JavaScript/fixture errors.

 query-one.
- Noncritical chart work is scheduled after first-pass race/results rendering to reduce initial blocking on slower machines.

## Precise limitations / next review cycle
1. This is the **first reviewable functional draft**, not evidence that all 27 planned charts, 10 tables and 6 visual modes in the blueprint have been completely implemented or visually approved. Finish the remaining component parity and accessibility walkthrough before production release.
2. Original 2021–2025 participant GPX bytes have not been checked into GitHub. Their evidence and 43 km comparison-group findings remain in the source registry. No old year borrows a 2025/2026 track.
3. Historical edition-wide finish-time performance changes are not presented as a single comparable trend without proven whole-course equivalence.
4. The 2026 organizer GPX files describe prospective 2026 courses; no invented 2026 race results are included.
5. Checkpoints with inadequate source coverage are gated. Target-plan segments without sufficient observed ratios use a labelled timing-distance fallback, not fabricated observations.
6. No externally scraped social-media runner portraits; initial avatars only.
7. EQ source artifact 11142571759 from run 36818159977 is time-limited: archive and freeze reproducibility before expiry. The web bundles are already committed.

## Downloadable review build

- [Package action 36839244517 — SUCCESS](https://github.com/Stayinhealthyrunning/satila-splits/actions/runs/36839244517); select `satila-first-draft-review` under Artifacts.
- Package contains exactly **44 static site files**, `satila-splits-first-draft-review.zip` (814,751 bytes before Actions artifact wrapping).
- Inner review ZIP SHA-256: `fce478cb97fb0eb3812b7f7df01b96772412030406450df5785103f9ad9abf0f`.
- Run `cd site && python -m http.server 8080` after extracting; open `http://localhost:8080/`. Keep PR #2 in draft and unmerged until review.

## Source and privacy boundaries

This static preview contains curated publicly displayed runner results only, with no auto-scraped athlete profile pictures; named portraits are deliberately out of scope. It excludes the internal SQLite file, raw EQ Timing responses and any unavailable participant-GPX files. A runner appearing in different years is **not** automatically linked as one person.

## Review instructions
Inspect `docs/index.html` in the build branch or download the static review ZIP from the project chat. To run an unpacked site, enter `site/` and use `python -m http.server 8080`; open `http://localhost:8080/`. Do not open the file via `file://` because dynamic JSON fetching needs an HTTP origin.

Do not merge automatically into Loppanalys.se. After project-owner review, complete outstanding blueprint parity and integrate via the site's published race catalogue.
