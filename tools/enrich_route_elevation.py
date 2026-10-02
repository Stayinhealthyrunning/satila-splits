#!/usr/bin/env python3
"""Offline elevation enrichment of SANITIZED published route JSON from local DEM GeoTIFFs.

Never creates original/athlete GPX, synthetic checkpoints, or source timestamps.
Inputs are public route geometry, not original participant records.
Candidate routes go to reports/elevation-candidates by default: review and explicitly
promote only after source licensing, coverage and vertical datum have been assessed.

Runtime dependency for real raster sampling: pip install rasterio
Unit-testable enrichment core (enrich_route) requires only Python stdlib.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Callable, Optional


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def enrich_route(
    route: dict,
    sample: Callable[[float, float], Optional[float]],
    *,
    dem_source_id: str,
    vertical_datum: str,
    input_sha256: str,
) -> tuple[dict, dict]:
    """Sample every published route coordinate; fail closed if any height is absent.

    sample(lat, lon) must return a finite elevation in metres, or None for NoData.
    No spatial interpolation across missing DEM coverage is allowed.
    Distances, route geometry, original GPX source SHA and timing remain unchanged.
    """
    points = route.get("points")
    if not isinstance(points, list) or len(points) < 2:
        raise ValueError("Route has fewer than two points")
    if not dem_source_id.strip() or not vertical_datum.strip():
        raise ValueError("DEM provenance and vertical datum are required")
    if len(input_sha256) != 64:
        raise ValueError("Input file SHA-256 is required")

    out = dict(route)
    enriched = []
    no_data_indices = []
    for i, point in enumerate(points):
        if not isinstance(point, list) or len(point) != 4:
            raise ValueError(f"Expected [distance_km, lat, lon, elev] at point {i}")
        km, lat, lon, existing = point
        if not all(isinstance(n, (int, float)) and math.isfinite(n) for n in (km, lat, lon)):
            raise ValueError(f"Invalid geographic point {i}")
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError(f"Invalid latitude/longitude at point {i}")
        if existing is not None:
            raise ValueError("Refusing to overwrite a route that already includes elevation")
        value = sample(float(lat), float(lon))
        if value is None or not isinstance(value, (int, float)) or not math.isfinite(value):
            no_data_indices.append(i)
            enriched.append([km, lat, lon, None])
        else:
            enriched.append([km, lat, lon, round(float(value), 2)])

    covered = len(points) - len(no_data_indices)
    qa = {
        "race_key": route.get("race_key"),
        "source_route_sha256": input_sha256,
        "source_gpx_sha256": route.get("source_sha256"),
        "dem_source_id": dem_source_id,
        "vertical_datum": vertical_datum,
        "points": len(points),
        "covered_points": covered,
        "coverage_fraction": round(covered / len(points), 6),
        "no_data_indices": no_data_indices,
        "status": "COMPLETE" if not no_data_indices else "BLOCKED_INCOMPLETE_DEM_COVERAGE",
    }
    if no_data_indices:
        # The live elevation plot currently cannot display partly-null DEM.
        # Never publish misleading dips to 0 metres for missing values.
        return out, qa

    out["points"] = enriched
    out["elevation_available"] = True
    out["elevation_provenance"] = {
        "type": "DEM_RECONSTRUCTED_TERRAIN",
        "source_id": dem_source_id,
        "vertical_datum": vertical_datum,
        "input_route_sha256": input_sha256,
        "method": "Per-coordinate sampling of local georeferenced DEM; no runner elevation measurement",
        "coverage_fraction": 1.0,
        "not_official_ascent_or_runner_altitude": True,
    }
    # Keep source_sha256 untouched: it identifies the original geometry GPX.
    return out, qa


class GeoTiffSampler:
    """Resolve points against one or more local rasters in their native CRS."""

    def __init__(self, paths: list[Path]):
        try:
            import rasterio
            from rasterio.warp import transform
        except ImportError as exc:
            raise SystemExit("DEM sampling requires rasterio: python -m pip install rasterio") from exc
        self.rasterio = rasterio
        self.transform = transform
        self.datasets = []
        for path in paths:
            ds = rasterio.open(path)
            if ds.crs is None:
                ds.close()
                raise ValueError(f"Raster missing horizontal CRS: {path}")
            if ds.count < 1:
                ds.close()
                raise ValueError(f"Raster has no elevation band: {path}")
            self.datasets.append(ds)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        for dataset in self.datasets:
            dataset.close()

    def __call__(self, lat: float, lon: float) -> Optional[float]:
        for ds in self.datasets:
            xs, ys = self.transform("EPSG:4326", ds.crs, [lon], [lat])
            x, y = xs[0], ys[0]
            if not (ds.bounds.left <= x <= ds.bounds.right and ds.bounds.bottom <= y <= ds.bounds.top):
                continue
            sample = next(ds.sample([(x, y)], indexes=1, masked=True))
            value = sample[0]
            if getattr(value, "mask", False) is not False:
                # masked scalar or masked constant
                if bool(value.mask):
                    continue
            n = float(value)
            if ds.nodata is not None and math.isclose(n, ds.nodata, abs_tol=1e-8):
                continue
            if math.isfinite(n):
                return n
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--routes", nargs="+", type=Path, required=True,
                        help="Existing sanitized docs/data/routes/*.json inputs")
    parser.add_argument("--dem", nargs="+", type=Path, required=True,
                        help="Local, licensed GeoTIFF DEM tile(s), in metres")
    parser.add_argument("--source-id", required=True,
                        help="Stable identifier for the specific DEM release, resolution and provider")
    parser.add_argument("--vertical-datum", required=True,
                        help="As documented by DEM provider, e.g. RH2000 (never guess)")
    parser.add_argument("--output-dir", type=Path, default=Path("reports/elevation-candidates"))
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    audit = []
    with GeoTiffSampler(args.dem) as sampler:
        for path in args.routes:
            raw = path.read_bytes()
            route = json.loads(raw)
            enriched, report = enrich_route(
                route, sampler, dem_source_id=args.source_id,
                vertical_datum=args.vertical_datum, input_sha256=sha256_bytes(raw),
            )
            audit.append(report)
            if report["status"] == "COMPLETE":
                output = args.output_dir / path.name
                if output.exists():
                    raise FileExistsError(f"Refusing to overwrite an existing candidate: {output}")
                output.write_text(
                    json.dumps(enriched, ensure_ascii=False, separators=(",", ":")) + "\n",
                    encoding="utf-8",
                )
                report["candidate_path"] = str(output)

    qa_file = args.output_dir / "DEM_QA.json"
    qa_file.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for row in audit:
        print(f"{row.get('race_key')}: {row['status']} ({row['covered_points']}/{row['points']} points)")
    print(f"QA report: {qa_file}")
    if any(row["status"] != "COMPLETE" for row in audit):
        raise SystemExit("DEM coverage incomplete: do not promote these routes")


if __name__ == "__main__":
    main()
