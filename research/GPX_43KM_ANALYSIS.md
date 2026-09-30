# 43 km GPX analysis — 2021–2025

Five Suunto/Sports Tracker route exports supplied by the project owner were inspected as participant race-day geometry.

## Privacy / raw-file handling

The source GPX files contain participant metadata in the GPX metadata block, including an author name and in some cases free-text race notes. The raw uploads are therefore **not committed to the public repository** in this first pass.

The source registry stores SHA-256 hashes and geometry statistics so the exact original files remain verifiable. A later import step should create route-only sanitized GPX assets if local geometry files are needed in the repository.

## Geometry summary

| Year | Points | Raw GPX polyline | 10 m simplified polyline | Start–finish gap |
|---|---:|---:|---:|---:|
| 2021 | 14,507 | 45.236 km | 43.893 km | 133 m |
| 2022 | 15,246 | 45.812 km | 44.378 km | 160 m |
| 2023 | 14,146 | 42.864 km | 41.408 km | 147 m |
| 2024 | 13,810 | 42.598 km | 41.325 km | 138 m |
| 2025 | 13,260 | 42.599 km | 41.344 km | 151 m |

These distances are **measurements of participant GPS polylines**, not canonical race distances. Dense forest GPS noise inflates raw polyline length; simplification reduces that noise but also shortens real trail curvature. Canonical distance must therefore come from a consistent route-processing method and verified course geometry.

Raw positive elevation gain from the participant files is deliberately not promoted to canonical data because device elevation noise and processing differ between years.

## Course-family finding

The geometry separates very clearly into two groups.

### 2021–2022
2021 versus 2022:
- 97.50% of bidirectional 20 m-sampled geometry lies within 25 m of the other trace.
- 98.53% lies within 50 m.

This is strong evidence that the two years used the same basic race-day course corridor.

Manual review by the participant has identified the following wrong turns:

#### 2021
- around **21 km** in the raw track: confirmed wrong turn. Geometry comparison suggests roughly **0.24 km** of extra raw distance, reaching about **115 m** from the 2022 corridor;
- around **30 km**: confirmed wrong turn. Geometry comparison suggests roughly **0.31 km** of extra raw distance, reaching about **120 m** from the 2022 corridor.

#### 2022
- around **22 km**: confirmed wrong turn, a clear out-and-back excursion adding roughly **0.66 km** of raw GPS distance and reaching about **348 m** from the 2021 corridor;
- the section around **6.9 km**, previously suspected as an anomaly, is **confirmed correct course** and must not be removed.

The raw GPX files must remain unchanged as source evidence.

For a clean 2021–2022 course candidate, neither participant file should be selected wholesale as the sole reference. Instead:
- use the **2022 corridor** through the two known 2021 wrong-turn locations;
- use the **2021 corridor** through the known 2022 wrong-turn location;
- retain the 2022 line around 6.9 km;
- cross-check the resulting composite against organizer/ITRA geometry before promoting it to canonical status.

### 2023–2025
2023 versus 2024:
- 99.13% within 25 m.
- 99.91% within 50 m.

2024 versus 2025:
- 99.01% within 25 m.
- 99.65% within 50 m.

This is strong evidence for one stable 2023–2025 race-day course family. The short 2024/2025 discrepancy around roughly 7 km is local and small compared with the full course.

### Major change: 2022 → 2023
Only 74.43% of the 2022/2023 bidirectional geometry lies within 25 m and 75.56% within 50 m.

The principal divergence begins at roughly 6.5–6.8 km from the participant start. The 2022 trace follows a large eastern loop before returning around 19–20 km, while the 2023 trace instead follows a substantially different southern loop and rejoins the common corridor around 16–18 km on that year's trace.

This is a genuine course redesign signal, not ordinary GPS drift: parts of the two alternatives are more than 3 km apart geographically.

## Canonical route strategy

Preserve all five original participant GPX files as evidence, but do not use raw GPS polylines directly as canonical course geometry.

For the early family:
- construct a corrected composite of **2021 + 2022**;
- remove only the three manually confirmed participant wrong turns;
- use the unaffected year's geometry to bridge each wrong-turn section;
- smooth GPS jitter conservatively after correction, not before.

For the later family:
- derive a consensus/centerline geometry from **2023, 2024 and 2025**;
- use conservative smoothing so GPS jitter is reduced without straightening true trail bends.

The result should be two clean comparison-route candidates:
- `trail43-2021-2022`
- `trail43-2023-2025`

They remain candidates until cross-checked against organizer and/or ITRA/Trace de Trail geometry.

## Current model

Do not yet call the groups exact canonical course versions. Use:

- comparison group A: **2021–2022**
- comparison group B: **2023–2025**

Promotion to exact course versions requires comparison with organizer GPX, ITRA/Trace de Trail geometry, or multiple independent participant traces.

## Next checks

1. Build a corrected and sanitized 2021–2022 composite route.
2. Build a smoothed 2023–2025 consensus route.
3. Match both candidates against ITRA/Trace de Trail and organizer GPX where available.
4. Identify canonical checkpoint coordinates and project them onto each course version.
