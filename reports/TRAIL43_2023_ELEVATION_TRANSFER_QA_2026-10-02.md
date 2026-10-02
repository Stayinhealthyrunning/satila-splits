# Sätila 43 km — 2023 elevation transfer from 2024 participant geometry

Date: 2026-10-02. Scope: display-only altitude. All 2023 race observations, segment times, horizontal geometry, original normalized sources and other edition routes remain unchanged.

## Geometric matching of 2023, 2024, 2025

For each published point, compute the shortest projected distance to every consecutive segment in the reference polyline. Use a local equirectangular approximation at 57.5°N, linear interpolation of reference elevation at the nearest location. Do **not** match by same percentage of total course distance, which can be wrong at overlaps/start–finish and on changed routes.

| Comparison (direction matters) | p50 | p95 | Maximum | Within 20 m |
|---|---:|---:|---:|---:|
| 2023 participant-derived geometry → 2024 participant geometry | 0.0 m | 9.68 m | 23.57 m | 99.39 % |
| 2024 participant geometry → 2023 participant-derived geometry | 0.97 m | 10.46 m | 28.03 m | 99.80 % |
| 2023 participant geometry → 2025/26 organizer geometry | 4.71 m | 16.87 m | 89.71 m | 96.84 % |
| 2024 participant geometry → 2025/26 organizer geometry | 5.19 m | 17.38 m | 89.71 m | 96.27 % |

Thus 2023 and 2024 are near-identical in the published GPS corridors, consistent with the owner's suggestion, but this **does not certify** that organizers declared exactly identical courses. 2025/26 has several local displacements reaching ~90 m (especially near the ~20 km area), so do not blindly copy its elevation array into 2023.

## Source and provenance

- **Target** `docs/data/routes/2023-trail43-participant.json`; 822 vertices, 41.873734 km; source checksum `0ea09c107612064a31c717462cebbfd092b6cefb728b051f529f7b8a27737695`.
- **Reference** `docs/data/routes/2024-trail43-participant.json`; 1,018 vertices, 41.948369 km; original 2024 participant source checksum `d83bfad962e94a69ed0ea53a0c063679478234cccd3a780d714900ae7640c4b4`.
- Reconstructed 2023 altitudes were interpolated from the **nearest geographic segment of the 2024 route**, with all match distances <24 m and 100% inside a 30 m acceptance limit. Values are rounded to 0.01 m for deterministic publication.
- 2023's original normalized source `data/normalized-gpx/trail43-2023-2025-normalized.json` and `.gpx` remain untouched, retaining the prior altitude series and source SHA-256 for audit.
- 2023 `[distance_km, latitude, longitude]` are **bit-for-bit JSON-value identical** to the prior normalized asset.
- This transfers a participant's **GPX-derived altitude** from 2024; it is not 2023 altimeter evidence, not an official organizer profile, and must not create official D+, timing passes or GPX runner positions.

## QA before and after (adjacent pairs within ≤100 m horizontal display distance)

| Measure | Original 2023 altitude | Spatially transferred 2024 altitude |
|---|---:|---:|
| Short adjacent altitude jump p95 | 18.8 m | 5.29 m |
| Short adjacent jumps >20 m | 26 | 1 |
| Largest short jump | 33.8 m | 21.09 m |
| Source timestamp/timing rows touched | No | No |

The residual 21.09 m change in one local region is not silently claimed to be surveyed terrain. This quality level is suitable for an **illustrative** elevation profile, not a certified ascent total.

## Release assertions

`tests/test_2023_trail43_spatial_height_transfer.py` reproduces each published 2023 altitude from 2024 source coordinates, verifies the original 2023 horizontal geometry and source SHA, requires max match below 24 m, bounds short-pair artefacts, and checks UI source disclosure. The existing multi-year browser regression also asserts the 2023 altitude label and visible method caveat at desktop/mobile widths.

No updates to `docs/data/bootstrap.json`, races, 2024 route or 2025 organizer route are authorized for this elevation-only correction.
