# Data

- `data/work/`: transient imports (ignored)
- `data/private/`: local/private source assets (ignored)
- `data/source/`: redistributable source assets and manifests
- `docs/data/`: browser-ready derived bundles

Every public derived value must retain a provenance path to source observations. Missing values remain missing; no split or status is fabricated.

## Accepted owner 43 km GPX source archive (2021–2025)

The owner supplied five authentic Suunto/Sports Tracker race-day GPX files.
Two metadata-free, normalized **participant-derived display corridors** have
been reconstructed from those originals and accepted for cartographic use.
They are not official organizer files or proof of year-to-year performance equivalence.

To permanently archive all seven exact source files, upload
`satila-43km-2021-2025-source-and-normalized.zip` into
`data/participant-gpx/` on `main` using **Add file → Upload files**.
Keep the ZIP intact; do not extract and upload its members one by one.

Expected ZIP SHA-256:
`1617c1e1fe96912409989f3844f89c52e3673e8386c44394f1e0f367dd8cd5dc`

The workflow `import-normalized-43km.yml` starts on that upload and verifies
all five original SHA-256 values and both normalized SHA-256 values. It then
generates metadata-only browser JSON for each year and commits it to main,
without changing EQ Timing results, recorded splits or stations, and dispatches
the standalone Pages deployment.

- 2021–2022 use the owner-accepted corrected participant corridor.
- 2023–2024 use the owner-accepted three-year consensus corridor.
- 2025 retains the verified organizer GPX as the **preferred site map**, while
  the separate accepted 2023–2025 normalized participant asset is also archived
  and published as source evidence.

The GPX names, sources, measured distances and historical-versus-reconstructed
hash distinction are recorded in the source ZIP manifest and
`config/course-versions.json`. The owner explicitly approved public
preservation of their own GPX originals; keep temporary export URL tokens
and unrelated connection traces out of GitHub.
