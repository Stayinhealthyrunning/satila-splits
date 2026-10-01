# Normalized 43 km route candidates

Two route-only GPX candidates have been generated from the verified participant tracks.

## 2021–2022

File: `Satila_Trail_43km_2021-2022_NORMALISERAD.gpx`

Method:
- use the 2022 participant geometry as the base because only one participant wrong turn is confirmed in that track;
- remove the 2022 out-and-back excursion around raw chainage 22 km by reconnecting the two points where the excursion leaves and returns to the course corridor;
- the removed raw excursion is about 760 m long and the rejoin points are only about 1.5 m apart;
- this also avoids the two confirmed 2021 participant wrong turns around 21 km and 30 km;
- retain the 2022 geometry around 6.9 km, which has been manually confirmed as correct;
- apply a conservative 3 m Douglas-Peucker simplification to reduce GPS jitter.

Result: approximately 44.415 km geometric polyline length and 1,091 points.

## 2023–2025

File: `Satila_Trail_43km_2023-2025_NORMALISERAD.gpx`

Method:
- mildly simplify each 2023, 2024 and 2025 track;
- align 2023 and 2025 monotonically to the 2024 route using dynamic time warping;
- at each aligned location choose the observed point with the smallest total distance to the other two tracks (medoid consensus), so an outlying GPS observation cannot pull the route away from an actually observed corridor;
- apply a final conservative 3 m simplification.

Result: approximately 41.595 km geometric polyline length and 944 points.

## Status

Both GPX files are **normalized analysis-route candidates**, not yet official/canonical course files. Their geometry should be cross-checked against organizer GPX and ITRA/Trace de Trail before promotion to canonical course versions.

No participant names, timestamps or other personal GPX metadata are present in the normalized route files.
