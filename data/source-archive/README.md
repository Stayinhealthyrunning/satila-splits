# Sätila EQ Timing – permanent source archive

The canonical public reconstruction input is `satila-eqtiming-full-source-2026-10-01.zip` (to be uploaded alongside this README).

- Source: GitHub Actions run `36818159977`, artifact ID `11142571759`, created 2026-10-01.
- This ZIP retains **all 422 files from `eqtiming-full/`**, for the years 2016–2019 and 2021–2025, and adds `SOURCE_MANIFEST.json` with per-file SHA-256 and byte counts.
- Committed ZIP size (Actions-generated): **5,181,913 bytes**.
- Committed ZIP SHA-256 (Actions-generated): `25b28550ea4b5ae1f2464f150ba8a16439b8cec4e9d9b1b4168d7dba4b288217`. The independently repackaged downloadable copy has identical 422 source members but different ZIP container bytes (SHA-256 `868770e34d892e6dbf792e3d04ee7848cc977fc236aee068d74eb936b00c7dc4`).
- The original temporary artifact also included 138 ancillary `eqtiming/` browser/network traces. They are **not** part of the reconstruction database and include access/connection negotiation tokens; they must not be committed publicly.
- The archive is stored outside `docs/` and is not a GitHub Pages site asset. Do not put personal access credentials or other non-race technical traces here.

## Validation

```bash
python -c "import hashlib,pathlib; p=pathlib.Path('data/source-archive/satila-eqtiming-full-source-2026-10-01.zip'); print(p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest())"
```

Expected for committed ZIP: `5181913 25b28550ea4b5ae1f2464f150ba8a16439b8cec4e9d9b1b4168d7dba4b288217`.

Then unpack the archive in a temporary directory and inspect `SOURCE_MANIFEST.json`. Do not replace the published, sanitized `docs/data/` with unprocessed source files.
