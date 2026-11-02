"""Race-day preflight: the verified 2026 event must not be auto-published or leak raw sources."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class Satila2026Preparation(unittest.TestCase):
    def test_2026_registered_as_pending_without_altering_frozen_catalog(self):
        catalog=json.loads((ROOT/"config/eqtiming-events.json").read_text(encoding="utf-8"))
        self.assertEqual(len(catalog["events"]),9)
        self.assertEqual([x["year"] for x in catalog["events"]], [2016,2017,2018,2019,2021,2022,2023,2024,2025])
        pending=[x for x in catalog["pending_events"] if x["year"]==2026]
        self.assertEqual(len(pending),1)
        event=pending[0]
        self.assertEqual(event["event_id"],82600)
        self.assertEqual(event["date"],"2026-11-07")
        self.assertEqual(event["url"],"https://live.eqtiming.com/82600")
        self.assertTrue(event["requires_private_registry_review"])
        self.assertEqual(event["publication_status"],"NOT_APPROVED")

    def test_no_2026_result_is_fabricated_in_public_static_site(self):
        bootstrap=json.loads((ROOT/"docs/data/bootstrap.json").read_text(encoding="utf-8"))
        self.assertFalse([e for e in bootstrap["editions"] if e["year"]==2026])
        self.assertFalse(list((ROOT/"docs/data/races").glob("2026-*.json")))

    def test_legacy_raw_capture_remains_disabled(self):
        workflow=(ROOT/".github/workflows/import-eqtiming.yml").read_text(encoding="utf-8")
        self.assertIn("if: ${{ false }}",workflow)
        self.assertIn("PRIVACY HOLD",workflow)


if __name__=="__main__":
    unittest.main()
