# GPX checkpoint – Sätila trail43, 2026-10-02

## Status
All five owner-supplied original Suunto/Sports Tracker GPX uploads from 2021–2025 recovered and checked for XML and route point counts. They are backed up as a ZIP in the owner's ChatGPT Library:

`/Sätila Splits/GPX källarkiv/satila-gpx-original-2021-2025-checkpoint.zip`

Library backup ZIP size **493826 bytes**, SHA-256 **15a71289d7935bb320f98a1b7ebf54b61e1ccf8185f549d1aec2273c5707d6cf**. The ZIP contains an `ORIGINAL_GPX_MANIFEST.json` and the five unmodified originals.

| Year | Original points | SHA-256 |
|---|---:|---|
| 2021 | 14507 | d07051fda67d4343ccf9ff49ec7ee8788b923965f14b127e5d7ffaac91a0c9d6 |
| 2022 | 15246 | b7bd4710327fae74d0478db5dbb1df80c3bb7f84c9d316fd9c2a86028486479c |
| 2023 | 14146 | 60b5f920d6f4e652db1760120f6d22bd1fcdea722edee46c83dc7d6f0c1e04da |
| 2024 | 13810 | d83bfad962e94a69ed0ea53a0c063679478234cccd3a780d714900ae7640c4b4 |
| 2025 | 13260 | f090e7d461e0ae53e06561c340b1a87bab30f10454e49ebaface2cd19468502b |

The original 2024 SHA equals the original published 2024 source in `config/source-registry.json`.

## Next restartable stages
1. Extract originals from Library checkpoint ZIP, no need to ask the owner to upload again.
2. Reconstruct **2021–2022 corrected composite**, method in `research/NORMALIZED_43KM_ROUTES.md`: 2022 corridor baseline, remove wrong out-and-back at raw ~22 km (~760 m), retain confirmed correct section around 6.9 km, bypass 2021 wrong turns; target historical reference ~44.415 km, 1091 simplified points. Previous normalized SHA (reference only, not assumed reproducible byte-for-byte): `21752f9d5aafe13cb40c72845f6c1e96e416fb785180f87b3c920fb8178b874c`.
3. Independently build **2023–2025 consensus** using DTW alignment and medoid choice, conservative final 3m simplification, target historical reference ~41.595 km / 944 points, historical SHA `e0fb4b648b48cd396f8922146e9ce27a20093b397d8c9413b4697b02bec45111`.
4. For each, write actual resulting file, source fingerprints, validation report and archive checkpoint *before* editing webpage. Never claim it was rebuilt unless verified.
5. Promote these OWNER-ACCEPTED NORMALIZED PARTICIPANT courses for year-scoped display 2021–22 and 2023–25, preserving source labels and EQ Timing-only real split calculations. Existing 2024 participant display and 2025 organizer source are not to be silently discarded. Update and test 27-edition route contract, then merge/deploy.

## Crash safety
One source family per short run and one saved artifact/checkpoint per stage. Do not attempt normalization, five editions' edits, full browser QA and deployment in one huge operation.
