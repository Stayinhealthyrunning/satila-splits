# Source-preserving removal of owner-rejected Grind timing point

2026-10-02. Active curated analysis only, no deletion/rewrite of the immutable original EQ Timing source archive.

The public EQ Timing export once listed an early 1.2-km measurement called Grind, but the project owner confirmed it must not count as an official race checkpoint in Sätila Splits. Unlike a mere CSS hide, we exclude the station UID and all associated TIME observations in every affected static race bundle, and permanently filter it from the source exporter (`tools/build_satila.py`). **We do not interpret any excluded Grind TIME as a legitimate intermediate passage.**

- 20 affected RaceEdition records: 2018–19 all three families; 2021 trail22/trail43 only; 2022–25 all three families.
- 7 untouched editions: all 2016–17, Ultra85 2021.
- Original public-source archive: **16,525 TIME observations** including **2,059 owner-excluded Grind**; original source evidence/fingerprints left unchanged.
- Curated, published analysis after exclusion: **14,466 TIME observations**; 27 editions, 3,272 results, 2,649 finishers, all finish times and all GPX files remain unchanged.
- `docs/data/races/*.json`: no Grind station metadata, no associated UID in splits. `docs/data/bootstrap.json` and `docs/data/coverage.json` recomputed station/split counts for all 20 editions. All runtime calculations derive new boundaries from the filtered per-edition source data.
- `tests/test_grind_exclusion_contract.py` exhaustively enforces the rule for all 27 editions; included in mandatory source release gate.
- Snapshot golden segments and synthetic source contracts updated; old pre-migration QA reports and raw archive remain historical evidence, not current methodology.

First actual 2025 analytical segments (using an explicitly illustrated race-start time origin, not inventing additional EQ Timing rows):

| Race | Previous two intervals | After owner exclusion | Recorded finisher TIME observations | Source-based median first passage |
|---|---|---|---:|---:|
| trail22 | Start–Grind–Skolan | Start–Skolan 9.6 km | 156 | 3513.975 s |
| trail43 | Start–Grind–(Tostared metadata only)–Torrås | Start–Torrås 16.2 km | 130 | 6392.97 s |
| ultra85 | Start–Grind–Navåsen | Start–Navåsen 19.4 km | 79 | 9279.26 s |

**Tostared remains metadata-only (0 TIME), not a fabricated checkpoint.** The first source-derived 2025/43 segment is Start→Torrås, not a subtraction of Grind timings; downstream checkpoint differences (e.g. Torrås→Almered) remain unchanged. No source row is reassigned to a neighboring station. Historical GPX geometries/höjder, registered results, and elapsed finish times remain identical.

**Do not reuse historical reports asserting a seven-segment Grind→Torrås bridge as current release truth.** Current release audit is this migration and its exact-commit source/browser test evidence.
