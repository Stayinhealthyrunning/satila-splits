# 43 km owner GPX source and reconstructed normalized route families

The exact five original Suunto GPX uploads, one per race day (2021–2025), are preserved at `data/participant-gpx/trail43-YYYY.gpx`. They are original race-day **participant recordings**, not official organizer files. The project owner explicitly approved storing these original personal GPX publicly. No Sports Tracker export URLs or session tokens are committed.

## Restored routes

| Normalized family | Accepted display years | Current normalized GPX | Geometry | Points | Current SHA-256 |
| --- | --- | --- | ---: | ---: | --- |
| 2021–2022 | 2021, 2022 | `trail43-2021-2022-normalized.gpx` | 44.309170 km | 1,090 | `2a681e80841ae008872e35d8f4ffd1617b80a94bebcbbb18881e52fd86af82d4` |
| 2023–2025 | 2023, 2024, 2025 | `trail43-2023-2025-normalized.gpx` | 41.873734 km | 822 | `0ea09c107612064a31c717462cebbfd092b6cefb728b051f529f7b8a27737695` |

The **earlier missing exports** were documented as approximately 44.415 km/1,091 points (2021–2022) and 41.595 km/944 points (2023–2025), and their historical original SHA-256 remains in `config/course-versions.json`. Those exact lost byte streams were not recovered. The current files are clearly identified as new, deterministically reproducible reconstructions from the exact original five uploads, **not** claimed to be byte-identical to the earlier exports.

### Reconstruction and limitations

Run `python tools/rebuild_owner_normalized_43.py` (requires `numpy` and `scipy`) from any location. GitHub CI regenerates these four source files and asserts a clean diff. The original raw GPX files are never edited.

- Early family: the 2022 participant GPX is used as the source corridor, avoiding the two known 2021 wrong turns. The 2022 out-and-back excursion between approximately 21.882 and 22.640 raw GPS km is removed, connecting recorded locations only about 1.49 metres apart. A conservative Douglas–Peucker reduction is applied.
- Late family: 2023 and 2025 are monotonically aligned with 2024 via DTW; for each anchor the medoid of the three actual observed locations is selected and conservatively simplified. The route is an illustrative consensus, not the measured motion of an athlete.
- No GPS timestamps, participant names, contact data, fabricated physical control coordinates or EQ Timing readings are placed in the normalized source exports or public `docs/data/routes/` geometry JSON.

### Publication policy

Three previously missing year-specific maps (2021–2023) are published as `docs/data/routes/YYYY-trail43-participant.json`, linked from the year catalog and coverage. The already accepted **2024 real participant route** and **2025 organizer-assumed route** remain the active display assets. The consensus normalizations are separately retained as accepted course-family evidence for both 2024 and 2025.

Neither GPX geodesic length nor an interpolated map cursor becomes an official timing axis. A runner's segment analysis still uses only valid observed EQ Timing endpoint TIME pairs; missing checkpoint observations are not fabricated.
