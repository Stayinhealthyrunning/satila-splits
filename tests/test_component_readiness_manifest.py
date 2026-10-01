#!/usr/bin/env python3
"""Contract for reports/COMPONENT_READINESS_MATRIX.json."""
from __future__ import annotations
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"reports"/"COMPONENT_READINESS_MATRIX.json"

def expected_ids():
    return (
      [f"D{i:02d}" for i in range(1,28)] +
      [f"T{i:02d}" for i in range(1,11)] +
      [f"K{i:02d}" for i in range(1,7)] +
      [f"P0.{i}" for i in range(1,6)]
    )

class ComponentReadinessManifest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=json.loads(REPORT.read_text(encoding="utf-8"))
        cls.items=cls.doc["components"]

    def test_every_blueprint_component_exactly_once(self):
        ids=[x["id"] for x in self.items]
        self.assertEqual(len(ids),48)
        self.assertEqual(len(ids),len(set(ids)))
        self.assertEqual(set(ids),set(expected_ids()))

    def test_statuses_are_explicit_and_evidence_is_locatable(self):
        allowed={"ready","gated","blocked_by_evidence","frontend_pending"}
        for item in self.items:
            self.assertIn(item["status"],allowed,item["id"])
            self.assertTrue(item["evidence"].strip(),item["id"])
            evidence=ROOT/item["test"]
            self.assertTrue(evidence.exists(),f"{item['id']}: missing evidence file {item['test']}")
            self.assertEqual(item["frontend_verification"],"pending_codex_candidate")

    def test_known_evidence_limits_are_not_accidentally_upgraded(self):
        by={x["id"]:x for x in self.items}
        self.assertEqual(by["K02"]["status"],"blocked_by_evidence")
        for key in ("K01","K03","K04","K05","P0.1","P0.2","P0.3","P0.4","P0.5"):
            self.assertEqual(by[key]["status"],"gated",key)
        self.assertEqual(by["T10"]["status"],"ready")
        self.assertEqual(self.doc["thresholds"],
                         {"median_n":5,"q25_q75_n":10,"q10_q90_n":20,"sex_median_n_each":5})

if __name__=="__main__":
    unittest.main(verbosity=2)
