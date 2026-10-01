# Source inventory

Working source map for Sätila Splits. Entries are evidence leads, not automatically canonical data.

## Official organizer
Sätila Trail publishes race information, historical result links and GPX material on satilatrail.se.

Historical race PMs indicate that GPX files have been published for multiple distances and that the ultra has used separate GPS tracking in several editions.

## EQ Timing
Known event IDs currently identified:

| Year | Event ID |
|---|---:|
| 2021 | 57767 |
| 2022 | 62409 |
| 2023 | 67695 |
| 2024 | 72918 |
| 2025 | 77864 |

These should be used to locate structured result/export data. Presence of an aid station in a PM must not be interpreted as an EQ split until the result payload confirms it.

## ITRA / Trace de Trail
Useful especially for 43 km and 85 km course history and homologated geometry. Historical Trace de Trail entries can retain route geometry after organizer links disappear.

## Tulospalvelu / GPS-seuranta
Potentially high-value source for actual race-day ultra tracks. Multiple participant tracker traces from the same year can be combined to identify consensus race-day geometry and filter individual wrong turns.

## Participant GPX
Five direct Suunto/Sports Tracker export links for 43 km, years 2021–2025, have been supplied by the project owner. They are treated as candidate VERIFIED_PARTICIPANT sources.

The opaque export URLs are intentionally not committed to this public repository until redistribution/publication provenance has been reviewed. The GPX files can be added later with source records and checksums.

## Verification principle
For participant activities, match:
1. runner identity where available,
2. exact race date,
3. advertised race,
4. approximate finish duration/distance,
5. route geometry,
6. official result where possible.

A single participant trace may contain a wrong turn and must not alone define an official course.
