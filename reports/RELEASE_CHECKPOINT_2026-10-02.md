# Sätila Splits — release checkpoint, 2026-10-02

## Ground truth
- First standalone release PR #13 merged to main: `c1aaf81c1636c19fbcdcf05deb1fc1de2e078795`.
- Last independently validated integrated functional SHA `93f375d614cb07438a13fa1be22b87a181d2698f`; Actions run `36979936937`, four of four PASS.
- 27 editions, 3,272 result rows (2,649 FINISHED, 128 DNF, 494 DNS, 1 UNKNOWN), 16,525 authentic public TIME observations.
- Public sanitized site is `docs/`. Historical route provenance restrictions remain in force; 2026 ultra geometry must not be reused for previous editions.
- Prepublish UX PR #14 merged into integration before PR #13; subsequent route and responsive fixes included in validated release.
- Older PR #7 and historical `reports/PRE_CODEX_FINAL_HANDOFF_2026-10-01.md` are not current starting points.

## Permanent original-data preservation
- Source artifact run `36818159977`, artifact ID `11142571759` (expires October 31, 2026).
- New `.github/workflows/preserve-eqtiming-source.yml` downloads the artifact and commits a checksum-manifested ZIP holding all **422** `eqtiming-full/` reconstruction files.
- Ancillary `eqtiming/` network traces are deliberately excluded from the public archive because they contain access/connection negotiation tokens, not required original competition data.
- Target `data/source-archive/satila-eqtiming-full-source-2026-10-01.zip` is outside `docs/`.
- **Acceptance:** verify the ZIP actually appears on `main`, inspect workflow log and manifest, validate 422 hashes, and retain a second copy. Creation of the workflow alone is not evidence that upload happened.
- Five original organizer GPX files should also receive long-term retention after separate licensing/metadata inspection.

## Standalone release
- `.github/workflows/deploy-pages.yml` runs source checks and packages only `docs/`, not the original archive.
- If repository Pages is disabled: open repository Settings > Pages, choose **GitHub Actions** as the build/deployment source and save. The standard `GITHUB_TOKEN` cannot perform first-time Pages enablement through `actions/configure-pages`.
- Verify the actual Pages deployment URL in workflow job output. Account custom domain `www.loppanalys.se` can be inherited by project Pages: do not guess a separate github.io address.
- Verify `index.html`, `data/bootstrap.json`, route assets, 27 editions and mobile layout on deployed address.
- Portal `Stayinhealthyrunning/Stayinhealthyrunning.github.io` Draft PR #8 (fourth Sätila card) **must remain unmerged** until the standalone site is live and owner approves it.

## Evidence-gated future enhancements (not publication blockers)
Checkpoint geographic coordinates, segment elevation gain/loss, historically comparable routes/records, and DNF location require independent source evidence. Never synthesize observations or project 2026 ultra routes backwards.
