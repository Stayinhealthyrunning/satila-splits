# Reconstructed elevation – reproducible offline pipeline

State: TOOLING ONLY. No historic 85 km elevation is published or claimed recovered by this PR.
The seven RouteGadget/Trace de Trail historic Ultra85 tracks have 2D geometry, not source elevations.

## Why a DEM

A 2026 organizer route or a neighboring 43 km athlete GPX only provides reference elevations
on its own geometry. Matching by percentage of race distance is unsafe because courses differ
by year and historical GPS sampling density varies. Sample a georeferenced terrain model
(DEM, ideally an appropriate Lantmäteriet dataset with documented resolution/vertical datum)
at each of the **actual published year's** latitude/longitude pairs.

## Usage

1. Obtain a properly licensed DEM GeoTIFF that covers the entire race geometry.
   Record provider, exact product/release, resolution, licence and vertical datum. Verify
   that pixel values are metres, not feet or an arbitrary raster index. Do not guess the datum.
2. Install the optional offline sampler dependency with python -m pip install rasterio.
3. Run from the repo root:

    python tools/enrich_route_elevation.py \
      --routes docs/data/routes/2018-ultra85-participant.json docs/data/routes/2019-ultra85-participant.json \
      --dem /PATH/TO/licensed_dem_tile_1.tif /PATH/TO/licensed_dem_tile_2.tif \
      --source-id "PROVIDER:DEM_PRODUCT:RELEASE:RESOLUTION" \
      --vertical-datum "DOCUMENTED_DATUM"

Add other year-specific JSON inputs after checking the raster extent. The script never downloads
external data, never writes inside docs/data, and refuses to overwrite existing candidate files.

Output:
- reports/elevation-candidates/<input-route-name>.json: only if **all** sampled points have
  valid finite heights and no existing altitude gets overwritten.
- reports/elevation-candidates/DEM_QA.json: sampled point counts, coverage, source inputs,
  DEM identifier/datum and NoData indices.
- Non-zero exit on incomplete DEM coverage; no partial elevation profile is promoted.

The elevation candidate preserves course geometry, distances, source GPX SHA, and timing
provenance. Its metadata marks every elevation as DEM_RECONSTRUCTED_TERRAIN, not a runner's
altimeter recording, not official organizers' gain (D+) and not an official timing control.

## Human QA before publishing

- Inspect DEM coverage and CRS/axis order. Compare sampled profiles with the organizer's
  2026 GPX at **spatially matching** sections to detect offset, false water levels or mismatched
  vertical references, never overwrite a year's course with a different year's geometry.
- Check for tile seams, NoData along lakes, implausible jumps, and zero/negative values that
  are legitimate terrain rather than missing samples. Verify licensing permits publishing
  derivative height sequences.
- Validate the produced JSON shape and the full browser elevation renderer on all widths,
  and source-and-route regression. Only then deliberately copy vetted candidate JSON into
  docs/data/routes and adjust route inventory/provenance.
- Prefer terrain elevation sourced from one consistent model for cross-year comparability.
  Differences in horizontal GPS quality and DEM resolution can still affect estimated gain.

The data-processing route here is independent of the user's Codex quota. Until a complete
licensed DEM is supplied, the honest public UI remains "Höjddata saknas".
