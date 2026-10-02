# Verified integrated release checkpoint – Sätila Splits

**First full green integrated build:** `d1bd5fd59a903cf9b2273446b5401a8db7cc574e`  
**All four jobs SUCCESS:** [GitHub Actions #36857454794](https://github.com/Stayinhealthyrunning/satila-splits/actions/runs/36857454794)  
**Draft review PR:** [#7](https://github.com/Stayinhealthyrunning/satila-splits/pull/7)  
**Original Codex safety branch:** `codex/saetila-complete-first-draft@a71a5ef` (untouched).

## Evidence – one exact source SHA

- Source/statistics/method/GPX/provenance/privacy/coverage package tests: **PASS**.
- Release-copy, real Back/Forward navigation, keyboard/mobile/visible-error states and pace-distance capability: **PASS**.
- Real Chromium two-way overview map ↔ elevation and synchronized two-runner H2H: **PASS 1440×900, 900×900, 390×844**.
- All 27 editions load and show appropriate route gating and source data: **PASS desktop and mobile**.
- Browser evidence: `2025-trail43` has **seven effective source-observed segments** (Tostared is metadata-only; real Grind→Torrås n=130); `2023-trail43` two sparse segments n=8 without fabricated quantiles; `2016-ultra85` only two actual women's finishers. **PASS desktop and mobile**.
- The CI ZIP is uploaded **only after all three preceding QA jobs pass**, with independently verified 44-file static allowlist and no raw private source.
- `satila-codex-integrated-review` artifact ID **11159440521**, outer upload sha256 `12a5be9735fb58ce44fbb97354b99402bce212922b20d7488bf62a5712517710`; inner static ZIP size **828330 bytes**, SHA-256 **`4d088ad75b39e80bba40a2a0d0d3ddbe98508d80012330e1f600ebd463773a16`**.
- Browser screenshots/log artifact `integration-browser-evidence`, ID **11159945426**.
- The source remains private, `main` and live Loppanalys.se remain unmodified, PR #7 remains Draft.

## What this proof does NOT certify

The integrated UI's entire design is not yet pixel-perfect against the approved board; Codex should finish visual/UX parities when its quota resets. There are also potential remaining physical-pace semantics in runner profile and the five standouts; these are the next isolated audit target. Every new functional commit after this exact SHA must rerun the complete CI and obtain a new package.

**Restore:** Git checkout `d1bd5fd59a903cf9b2273446b5401a8db7cc574e` in a temporary working directory (not reset the owner's Codex branch) if a later regression appears.
