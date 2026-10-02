# GPX import ready — 2026-10-02

Previous chats crashed repeatedly during normalization and integration. The work has been split into durable checkpoints.

## Already complete
- Original 2021–2025 owner-supplied Suunto GPX recovered and individually SHA-256 verified.
- Two new normalized analysis corridors generated: **2021–2022 44.30917 km / 1090 points**; **2023–2025 41.873734 km / 822 points**.
- These are new reconstructions: do not claim identical bytes or exact equality with September's missing GPX exports.
- Full ZIP (originals, normalized GPX, JSON, compressed route representations, reconstruction manifest) saved in owner's ChatGPT Library at `/Sätila Splits/GPX källarkiv/satila-43km-source-and-normalized-2021-2025.zip`.
- The ZIP has SHA-256 `3427a19a066abdef1b1c60dcb37a67015781af406dbf0988c32e1e63a451828c`; original files have pinned hashes in `tools/import_owner_normalized_43.py`.

## Pending exactly one binary transfer
GitHub's connected UTF-8 write API does not ingest a local binary ZIP file from ChatGPT's compute filesystem. Upload the Library/downloaded **exact** ZIP as:
`data/source-archive/satila-43km-source-and-normalized-2021-2025.zip` on `main`.

The `.github/workflows/import-owner-normalized-43.yml` automatically runs when this exact file is committed. It verifies ZIP SHA-256, all five originals, both compressed normalized files, point counts and lengths. It then imports the accepted **2021/2022 normalized early corridor** to separate edition-locked JSON maps, and the **2023–2025 consensus corridor** to the 2023 map. Existing separately validated 2024 GPX and official 2025 organizer GPX remain untouched but the entire normalized provenance set is preserved in ZIP. All 2021–2025 trail43 editions consequently have a linked map. The normal full source QA runs before a bot commit; the ordinary Pages deployment is triggered by changes to `docs/`.

If an import run fails, inspect that one Actions run; source package is already versioned and any retry is deterministic. Do not re-download Suunto links, re-upload five individual GPX, or rebuild normalized routes unless a specific integrity assertion fails.

Portal PR #8 remains independent and unmerged pending owner review.
