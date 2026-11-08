"""Regression: a source rebuild must not put raw participant SQLite in public Git.

Only synthetic paths are used. No EQ Timing data or private registry required.
"""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from build_satila import parse, require_private_source_build_output


class PrivateBuildOutputGuardTests(unittest.TestCase):
    def test_rejects_any_path_inside_public_repository(self):
        for dest in (ROOT,ROOT/"docs",ROOT/"docs"/"data",ROOT/"data"/"work"):
            with self.subTest(dest=dest):
                with self.assertRaisesRegex(RuntimeError,"Private source build required"):
                    require_private_source_build_output(dest)

    def test_allows_external_private_staging_path(self):
        with tempfile.TemporaryDirectory() as td:
            external=Path(td)/"source-stage"
            self.assertEqual(require_private_source_build_output(external),external.resolve())

    def test_parse_aborts_before_reading_sensitive_inputs_or_creating_sqlite(self):
        dest=ROOT/"docs"/"data"
        # All inputs are intentionally nonexistent: guard must run first.
        with self.assertRaisesRegex(RuntimeError,"Private source build required"):
            parse(Path("/unavailable-source"),dest,Path("/unavailable-config"))


if __name__=="__main__":
    unittest.main()
