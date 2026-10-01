#!/usr/bin/env python3
"""Privacy-safe static review-package manifest contract (no private source needed).

Expected to run independently of Codex frontend updates. Adding a new asset
requires explicitly updating this allowlist and release review, so an unrelated
raw source file cannot silently join the public GitHub Pages or review ZIP.
"""
from __future__ import annotations
import hashlib
import json
import pathlib
import unittest
from zipfile import ZipFile,ZIP_DEFLATED

ROOT=pathlib.Path(__file__).resolve().parents[1]
SITE=ROOT/"docs"
ASSETS={
 "assets/app.js","assets/analytics-extra.js",
 "assets/style.css","assets/style-extra.css",
 "assets/hero.webp","assets/design-reference.webp",
}
MANIFESTS={
 "data/bootstrap.json","data/coverage.json",
 "data/route-inventory.json","data/source-fingerprints.json",
}
EXPECTED_ROUTE={
 "data/routes/trail5-2025-2026.json",
 "data/routes/trail10-2025-2026.json",
 "data/routes/trail22-2025-2026.json",
 "data/routes/trail43-2025-2026.json",
 "data/routes/ultra85-2026.json",
}
BANNED_SUFFIXES={".gpx",".fit",".tcx",".kmz",".kml",".sqlite",".db",".zip",".gz",
                 ".tar",".b64",".env",".csv",".xlsx",".parquet",".log",".py"}

def expected_paths():
    catalog=json.loads((SITE/"data/bootstrap.json").read_text(encoding="utf-8"))["editions"]
    assert len(catalog)==27
    races={"data/races/"+e["race_key"]+".json" for e in catalog}
    assert len(races)==27
    return {"index.html","DATA_MODEL.md"}|ASSETS|MANIFESTS|EXPECTED_ROUTE|races

def actual_paths():
    return {p.relative_to(SITE).as_posix() for p in SITE.rglob("*") if p.is_file()}

def verified_manifest():
    want=expected_paths()
    have=actual_paths()
    missing=want-have; unexpected=have-want
    if missing or unexpected:
        raise AssertionError(f"Unexpected review distribution: missing={sorted(missing)} extra={sorted(unexpected)}")
    for name in have:
        p=pathlib.PurePosixPath(name)
        if p.is_absolute() or ".." in p.parts or any(part.startswith(".") for part in p.parts):
            raise AssertionError(f"Unsafe relative path: {name}")
        if p.suffix.lower() in BANNED_SUFFIXES:
            raise AssertionError(f"Raw/private archive in publication: {name}")
    return {name:hashlib.sha256((SITE/name).read_bytes()).hexdigest() for name in sorted(have)}

class ReviewPackageContract(unittest.TestCase):
    def test_allowlisted_static_package_contains_only_intended_content(self):
        m=verified_manifest()
        self.assertEqual(len(m),44)
        self.assertEqual(len([p for p in m if p.startswith("data/races/")]),27)
        self.assertEqual(len([p for p in m if p.startswith("data/routes/")]),5)

    def test_review_zip_paths_are_static_and_cannot_escape_site(self):
        m=verified_manifest()
        with ZipFile(pathlib.Path("/tmp")/"satila-review-audit-allowlist.zip","w",ZIP_DEFLATED) as z:
            for path in m:z.write(SITE/path,"site/"+path)
            z.writestr("README.txt","Private review-only static bundle; not the raw source archive.\n")
        zpath=pathlib.Path("/tmp")/"satila-review-audit-allowlist.zip"
        try:
            with ZipFile(zpath) as z:
                names=z.namelist()
                self.assertEqual(set(names),{"site/"+x for x in m}|{"README.txt"})
                for n in names:
                    pure=pathlib.PurePosixPath(n)
                    self.assertFalse(pure.is_absolute() or ".." in pure.parts,n)
                    if n.startswith("site/"):
                        key=n[5:]
                        self.assertEqual(hashlib.sha256(z.read(n)).hexdigest(),m[key])
        finally:
            zpath.unlink(missing_ok=True)

if __name__=="__main__":
    unittest.main(verbosity=2)
