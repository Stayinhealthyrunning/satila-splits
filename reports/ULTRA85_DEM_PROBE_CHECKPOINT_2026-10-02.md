# Historical Ultra85 – first real DEM sampling checkpoint (2026-10-02)

## Execution
- GitHub Actions run: https://github.com/Stayinhealthyrunning/satila-splits/actions/runs/37018604054
- Run conclusion: **SUCCESS**, job `ultra85-dem-research`.
- Artifact: `ultra85-copernicus-dsm-provisional-20261002` (ID `11232656174`, retained 30 days).
- Seven private-source-derived but publicly sanitized *year-specific* route JSONs sampled in a temporary runner only; production `docs/data/routes/` on `main` was **not changed**.
- Copernicus DEM GLO-30 Public (2021 release) **digital surface model**, tile `Copernicus_DSM_COG_10_N57_00_E012_00_DEM.tif` downloaded from the public AWS `copernicus-dem-30m` bucket.
- Tile SHA-256: `4a5eef5035a20fc434ea64af82e0565f52777cb36016ae209223bee024404eba`.
- CRS EPSG:4326, dimensions 2400x3600; tile bounds lon 11.9997916667..12.9997916667; lat 57.0001388889..58.0001388889; vertical reference from Copernicus specification: EGM2008 (EPSG:3855); heights in meters.
- Workflow invokes `tools/enrich_route_elevation.py` without external credentials; candidate output and `DEM_QA.json` available in the Actions artifact.

## Completeness (technical point coverage only)

| Year | Published map coordinates sampled | Valid DEM elevations | Observed DSM sample min–max (m) |
|---|---:|---:|---:|
| 2018 | 1,618 | 1,618 | 13.50–181.79 |
| 2019 | 1,345 | 1,345 | 13.50–181.72 |
| 2021 | 964 | 964 | 13.50–181.79 |
| 2022 | 1,607 | 1,607 | 13.50–183.62 |
| 2023 | 796 | 796 | 13.50–181.72 |
| 2024 | 1,158 | 1,158 | 13.50–179.13 |
| 2025 | 856 | 856 | 13.50–191.16 |
| **Total** | **8,344** | **8,344** | **100% coverage** |

## Strict QA limitations before publication

**DO NOT MERGE candidate elevations into published routes automatically.** 100% point coverage means only that every map coordinate intersected finite elevation cells. Copernicus GLO-30 is a **DSM (surface including vegetation/buildings)**, not a bare-earth ground model. Its source EGM2008 vertical datum must not be silently mixed with Swedish RH2000 or potentially unknown elevations in organizer GPX. Inspect lake/water editing, forest/tree effects, slope spikes, pixel quantization, course-to-DEM horizontal offset, and licensing/attribution for derived profiles. Independently cross-check spatially matching sections with the 2026 organizer course but do not claim they have identical geometry or comparable elevation datum.

A later vetted release should distinguish reconstructed *DSM surface elevation* from original recorded GPX altitude and mark it as non-official; for bare-earth trail profile prefer Lantmäteriet's Markhöjdmodell if authorized/downloadable. Do not calculate official D+ directly from raw sampled heights without noise filtering and metric validation.

Source links:
- https://registry.opendata.aws/copernicus-dem/
- https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM
