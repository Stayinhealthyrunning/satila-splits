# Data

Data is separated by provenance and transformation stage.

## Planned layout

- `raw/results/` — unmodified official result exports/payloads
- `raw/gpx/` — retained GPX assets when redistribution/storage is appropriate
- `raw/docs/` — race PMs and other source documents when appropriate
- `derived/` — reproducible generated datasets; ignored by Git by default
- `work/` — temporary processing output; ignored by Git
- `private/` — local-only source material that must not be committed

For every source asset, record provenance in the source registry or a manifest before using it as canonical input.
