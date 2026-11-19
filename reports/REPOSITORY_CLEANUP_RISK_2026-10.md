# Sätila cleanup risk classification — 2026-10

Baseline: clean `origin/main` at `62ce08947a882c5a6b41f55ba7ac848b9f5f33b8`.
The classification is conservative and contains no participant data.

## Classification

| candidate group | class | evidence | action |
|---|---|---|---|
| `docs/data/`, `data/`, `config/` public exports and race contracts | D | loaded by `docs/index.html`, release scripts and browser/unit tests | retain |
| `data/source-archive/`, private-restore action and `tools/restore_private_43_gpx.py` | B/D | private-source boundary and hash-verified QA path; public raw originals are forbidden | retain; never copy originals to public Git |
| `tools/fetch_*`, `inspect_*`, `install_*`, `rebuild_*` source tools | D/E | source/provenance pipeline and historical-route reconstruction; no deadness proof without private fixtures | retain pending owner review |
| `reports/BUILD_*`, `FINAL_*`, `PRE_*`, `SOURCE_*`, `GPX_*`, `comparison-*` | D/E | referenced as handoff/provenance evidence by README, workflows and audits; historical evidence is not disposable by age/name | retain |
| `.github/workflows/guard-public-raw-sources.yml`, `privacy-registry.yml`, `source-integrity.yml`, `restored-43km-qa.yml` | B/D | active privacy, source and private-restore gates | retain and run in CI |
| `.github/workflows/privacy-history-rehearsal.yml`, `prepare-support-pr-cleanup.yml`, `verify-sanitized-history.yml`, `purge-legacy-raw-ref-history.yml` | B/E | disposable history audits and guarded legacy sanitation; old refs/support cleanup are explicitly out of scope | retain unchanged; separate owner approval required for execution |
| `tests/browser_*`, `tests/test_*` and `reports/*qa*` | D | release, browser and contract coverage; tests are not dead merely because local fixtures are absent | retain |
| `reports/S11_FIRST_DRAFT_REVIEW.md` and similarly named historical notes | E | historical reports may contain decisions/evidence not referenced by code; no owner-approved archival policy exists | retain until explicit archival decision |

## Result

No tracked class-A removal or class-C consolidation is proven safe on current
`main`. There are no byte-identical tracked groups in this checkout. The
Windows `WinError 5` in the release-candidate run is an environment blocker,
not evidence that route or GPX code is redundant. No files were deleted and no
contracts, source paths, GDPR controls, or Pages behavior changed.

## Required next verification

Run the existing release workflow on a runner with writable TEMP/TMP and the
documented private restore. Compare the exact head SHA, protected totals,
public export and browser contract before considering any A/C change.
