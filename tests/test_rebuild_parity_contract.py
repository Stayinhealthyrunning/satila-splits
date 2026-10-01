#!/usr/bin/env python3
"""Contract tests for the independent clean re-export checksum comparator."""
from __future__ import annotations
import sys
import tempfile
import json
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from audit_rebuild_parity import verify

def write(root,name,obj):
    p=root/name
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,separators=(",",":")),encoding="utf-8")

class RebuildParityContract(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.pub=self.root/"published"
        self.new=self.root/"rebuilt"
        self.pub.mkdir();self.new.mkdir()
        self.original=[{"family":"trail43","source_filename":"Sätila Trail 43 - 2026.gpx",
                        "source_sha256":"4b10bee2201e8f2493a1bf564c1603c5431c123fdc8d19dfb432655fb04ee827",
                        "edition_references":[2025,2026]}]
        write(self.pub,"route-inventory.json",self.original)
        write(self.new,"route-inventory.json",self.original)
        write(self.pub,"races/2025-trail43.json",{"race_key":"2025-trail43","results":[1]})
        write(self.new,"races/2025-trail43.json",{"race_key":"2025-trail43","results":[1]})

    def tearDown(self):
        self.tmp.cleanup()

    def test_identical_json(self):
        result=verify(self.pub,self.new)
        self.assertTrue(result["pass"],result)
        self.assertEqual(result["byte_identical_files"],2)

    def test_backup_ascii_rename_only_is_permitted(self):
        normalized=[{**self.original[0],"source_filename":"Satila Trail 43 - 2026.gpx"}]
        write(self.new,"route-inventory.json",normalized)
        result=verify(self.pub,self.new)
        self.assertTrue(result["pass"],result)
        self.assertEqual(result["byte_identical_files"],1)
        self.assertEqual(result["filename_only_normalized_files"],["route-inventory.json"])

    def test_changed_gpx_checksum_is_fatal(self):
        normalized=[{**self.original[0],"source_filename":"Satila Trail 43 - 2026.gpx","source_sha256":"0"*64}]
        write(self.new,"route-inventory.json",normalized)
        self.assertFalse(verify(self.pub,self.new)["pass"])

    def test_changed_edition_links_are_fatal(self):
        normalized=[{**self.original[0],"source_filename":"Satila Trail 43 - 2026.gpx","edition_references":[2026]}]
        write(self.new,"route-inventory.json",normalized)
        self.assertFalse(verify(self.pub,self.new)["pass"])

    def test_modified_race_results_are_fatal(self):
        write(self.new,"races/2025-trail43.json",{"race_key":"2025-trail43","results":[2]})
        self.assertFalse(verify(self.pub,self.new)["pass"])

    def test_missing_json_is_fatal(self):
        (self.new/"races/2025-trail43.json").unlink()
        self.assertFalse(verify(self.pub,self.new)["pass"])

if __name__=="__main__":
    unittest.main(verbosity=2)
