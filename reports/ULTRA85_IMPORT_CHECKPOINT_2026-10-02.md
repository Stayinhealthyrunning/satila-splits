# Ultra85 historic route checkpoint — 2026-10-02

Status: **SEVEN ROUTES PREPARED; NOT YET CONNECTED TO BOOTSTRAP OR PUBLISHED**.
Main at start of task: `f267b47cd050a642b786e313002f98f1ebb7ab61`.
Owner-approved original RouteGadget participant recordings (race-day dates) exist for 2018, 2019, 2021, 2022, 2023, 2024, 2025, in private ChatGPT Library `/Sätila Splits/GPX källarkiv/`. Original raw GPX must NOT go into public `docs/`.

Durable release ZIP: `/Sätila Splits/GPX källarkiv/satila-ultra85-route-release-2026-10-02.zip`, also locally `/mnt/data/satila-ultra85-route-release-2026-10-02.zip` as of 2026-10-02. ZIP integrity validated: 11 files, no error. Contains privacy-sanitized route JSON for seven years, README integration steps, source manifest, cross-year geometry comparison, and reproducible builder.

| year | sanitized JSON file | displayed geometry km | display points |
| --- | --- | ---: | ---: |
| 2018 | 2018-ultra85-participant.json | 84.147947 | 1618 |
| 2019 | 2019-ultra85-participant.json | 81.151690 | 1345 |
| 2021 | 2021-ultra85-participant.json | 82.775276 | 964 |
| 2022 | 2022-ultra85-participant.json | 84.210529 | 1607 |
| 2023 | 2023-ultra85-participant.json | 81.048957 | 796 |
| 2024 | 2024-ultra85-participant.json | 83.364334 | 1158 |
| 2025 | 2025-ultra85-participant.json | 81.413504 | 856 |

The GPS geometry is participant-derived only. No identity or timestamps are present in published JSON. Elevation is null in every point; do not fabricate elevations. Observed GPS distances are not official course lengths; inter-year timing comparability is not approved. 2026 organizer route MUST remain separate.

To complete:
1. Copy seven `docs/data/routes/<year>-ultra85-participant.json` files from the release ZIP to this branch.
2. For each corresponding `<year>-ultra85` entry in `docs/data/bootstrap.json`, set `route_status:participant_track_display_only`, `route_file:routes/<year>-ultra85-participant.json`, `route_source_sha256` from the route JSON, `measured_route_geometry_km` from route JSON, `course_version:<year>-ultra85-participant-display-not-canonical`.
3. Confirm frontend tolerates null elevations (map available even when timing observations are partial; elevation graph may say no altitude data), run data/tests and mobile QA.
4. Commit as small checkpoints; only merge/publicize after validations.

Sources are not timing references. Replay must continue to use EQ Timing observed splits exclusively. Full seven-course comparison report resides within release ZIP.
