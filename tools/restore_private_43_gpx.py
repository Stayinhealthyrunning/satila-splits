#!/usr/bin/env python3
"""Hash-verified restoration of five private Sätila participant originals.

Never logs identity content, file names, personal GPS samples or hash strings.
The publicly deployed routes remain the separately approved normalized assets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "trail43-2021.gpx": "d07051fda67d4343ccf9ff49ec7ee8788b923965f14b127e5d7ffaac91a0c9d6",
    "trail43-2022.gpx": "b7bd4710327fae74d0478db5dbb1df80c3bb7f84c9d316fd9c2a86028486479c",
    "trail43-2023.gpx": "60b5f920d6f4e652db1760120f6d22bd1fcdea722edee46c83dc7d6f0c1e04da",
    "trail43-2024.gpx": "d83bfad962e94a69ed0ea53a0c063679478234cccd3a780d714900ae7640c4b4",
    "trail43-2025.gpx": "f090e7d461e0ae53e06561c340b1a87bab30f10454e49ebaface2cd19468502b",
}


def integrity(path: Path) -> tuple[int, str]:
    checksum = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            size += len(chunk)
            checksum.update(chunk)
    return size, checksum.hexdigest()


def restore(private_root: Path, output_root: Path) -> int:
    folder = private_root.resolve() / "satila" / "participant-gpx-original"
    manifest_file = folder / "SOURCE_MANIFEST.json"
    if not manifest_file.is_file() or manifest_file.is_symlink():
        raise ValueError("Private Sätila manifest is missing")
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    rows = manifest.get("files")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED):
        raise ValueError("Private Sätila GPX manifest has wrong cardinality")
    names = [row.get("path") for row in rows if isinstance(row, dict)]
    if len(names) != len(EXPECTED) or set(names) != set(EXPECTED):
        raise ValueError("Private Sätila manifest has unapproved source paths")
    if any(names.count(name) != 1 for name in names):
        raise ValueError("Duplicate private source in manifest")
    verified = []
    for row in rows:
        name = row["path"]
        original = folder / name
        if not original.is_file() or original.is_symlink():
            raise ValueError("Required private participant GPX unavailable")
        n, digest = integrity(original)
        if digest != EXPECTED[name] or row.get("sha256") != digest or row.get("bytes") != n:
            raise ValueError("Private participant GPX integrity mismatch")
        verified.append((name, original, n, digest))
    output_root.mkdir(parents=True, exist_ok=True)
    for name, original, n, digest in verified:
        target = output_root / name
        if target.exists() and integrity(target) == (n, digest):
            continue
        with tempfile.NamedTemporaryFile(dir=output_root, prefix=".gpx-restore-", delete=False) as tmp:
            staged = Path(tmp.name)
        try:
            shutil.copyfile(original, staged)
            if integrity(staged) != (n, digest):
                raise ValueError("Restored participant GPX failed integrity verification")
            os.replace(staged, target)
        finally:
            staged.unlink(missing_ok=True)
    if any(integrity(output_root / name) != (n, digest) for name, _, n, digest in verified):
        raise ValueError("Verified participant GPX restore incomplete")
    return len(verified)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-root", type=Path, required=True)
    args = parser.parse_args()
    count = restore(args.private_root, ROOT / "data" / "participant-gpx")
    print(f"Private Sätila participant GPX restored and verified: {count}/{len(EXPECTED)}")


if __name__ == "__main__":
    main()
