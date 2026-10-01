# S0 source lock – Sätila Splits
Date: 2026-10-01

- Base main: `ee3db94d84de760f59c7a4022ecaff95769a5b21`.
- Source foundation selectively preserved from unmerged PR #1 / `setup/foundation`: source registry, normalized 43 km candidate metadata, provenance analysis, AGENTS, data model, GPX downloader. Existing newer EQ Timing event registry and public-station importer on main remain authoritative.
- EQ Timing archive downloaded from successful run [36818159977](https://github.com/Stayinhealthyrunning/satila-splits/actions/runs/36818159977), artifact `satila-eqtiming-raw-36818159977` ID `11142571759`, 6.4 MiB ZIP, public EQ event/contestant/station/paginated result payloads for 2016–2019 and 2021–2025.
- Normalization checked locally against archive: 27 supported editions (3 families × 9 years), 3,272 unique race appearances, 2,649 verified FINISHED, 16,525 actual TIME station-passages (not 16,525 distinct runners). This is a build-stage check; preserve detail coverage reports.
- Five official organizer 2026 GPX available locally for 5/10/21/43/85; reuse assumption 2025→2026 for 5/10/21/43 only, separate 85/2026.
- Original raw participant GPX files from prior chats are not in current runtime. Their hashes/evidence from PR #1 are preserved; do not pretend those files have been committed.
- No automatic third-party participant profile images.
