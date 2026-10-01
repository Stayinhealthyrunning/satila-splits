# Browser checkpoint 2026-10-01

Verified locally with the actual 27 committed race bundles, 3272 appearances and a fully offline Chromium fixture. Tested 1440x900, 900x900, 390x844. All three race families, 2016/2025 switching, available 2025 route gating, missing historical route status and real individual profile with insights passed. No browser exceptions, missing JSON, or document overflow. A tablet podium grid overflow was detected and corrected. GitHub Actions workflow frontend-regression.yml now runs this test independently and uploads screenshots.

This is a QA checkpoint, not final S11 approval. Historical participant route files and full feature parity still require work.
