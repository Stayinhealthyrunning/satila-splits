#!/usr/bin/env python3
"""Verify the frozen public race archive's reproducibility metadata.

Does not fetch source files or publish raw contestant JSON. The fingerprint
manifest is immutable evidence to use when restoring the private raw artifact.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"docs"/"data"
DIGEST=re.compile(r"^[0-9a-f]{64}$")

def read(p):
    return json.loads(p.read_text(encoding="utf-8"))

class SourceChainOfCustody(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=read(ROOT/"config"/"eqtiming-events.json")
        cls.meta=read(DATA/"bootstrap.json")
        cls.fingerprints=read(DATA/"source-fingerprints.json")
        cls.route_inventory=read(DATA/"route-inventory.json")

    def test_frozen_event_catalog_and_fingerprints_agree(self):
        events=self.catalog["events"]
        self.assertEqual(len(events),9)
        self.assertEqual(set(self.fingerprints),{str(e["year"]) for e in events})
        self.assertEqual(len({e["year"] for e in events}),9)
        self.assertEqual(len({e["event_id"] for e in events}),9)
        for ev in events:
            fp=self.fingerprints[str(ev["year"])]
            self.assertEqual(fp["event_id"],ev["event_id"])
            self.assertRegex(fp["event_json_sha256"],DIGEST)
            self.assertEqual(ev["url"],f"https://live.eqtiming.com/{ev['event_id']}")
            self.assertRegex(ev["date"],r"^20\d{2}-\d{2}-\d{2}$")

    def test_public_edition_lineage_matches_catalog_and_source_url(self):
        events={e["year"]:e for e in self.catalog["events"]}
        self.assertEqual(len(self.meta["editions"]),27)
        for ed in self.meta["editions"]:
            source=events[ed["year"]]
            self.assertEqual(ed["event_id"],source["event_id"])
            self.assertEqual(ed["date"],source["date"])
            self.assertEqual(ed["source_url"],source["url"])
            race=read(DATA/"races"/f"{ed['race_key']}.json")
            self.assertEqual(race["source_url"],source["url"])
            self.assertEqual(race["event_id"],source["event_id"])
            self.assertEqual(race["year"],source["year"])
            self.assertEqual(race["family"],ed["family"])
            self.assertIsInstance(race["leg_uid"],int)
            self.assertGreater(race["leg_uid"],0)

    def test_organizer_route_sources_are_checksum_identified(self):
        official=[v for v in self.route_inventory if v.get("type")=="OFFICIAL_ORGANIZER"]
        self.assertEqual(len(official),5)
        families=set()
        for route in official:
            fam=route["family"]
            self.assertNotIn(fam,families)
            families.add(fam)
            self.assertRegex(route["source_sha256"],DIGEST)
            self.assertTrue(route["source_filename"].lower().endswith(".gpx"))
            self.assertGreater(route["source_points"],20)
            refs=route["edition_references"]
            self.assertEqual(refs,[2026] if fam=="ultra85" else [2025,2026])

    def test_source_bytes_are_not_leaked_with_published_fingerprint(self):
        fingerprints=read(DATA/"source-fingerprints.json")
        self.assertEqual(set(fingerprints),{"2016","2017","2018","2019","2021","2022","2023","2024","2025"})
        for fp in fingerprints.values():
            self.assertEqual(set(fp),{"event_id","event_json_sha256"})
            self.assertIsInstance(fp["event_id"],int)
            self.assertRegex(fp["event_json_sha256"],DIGEST)
        for item in self.route_inventory:
            self.assertNotIn("raw_gpx",item)
            self.assertNotIn("participant_gpx",item)

if __name__=="__main__":
    unittest.main(verbosity=2)
