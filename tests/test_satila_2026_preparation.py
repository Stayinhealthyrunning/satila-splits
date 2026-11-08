"""Sätila 2026 source state: never invent results or enable legacy raw import."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"docs/data"


class Satila2026Preparation(unittest.TestCase):
    def test_pending_or_published_2026_is_exclusive_and_source_verified(self):
        catalog=json.loads((ROOT/"config/eqtiming-events.json").read_text(encoding="utf-8"))
        self.assertEqual([x["year"] for x in catalog["events"]],
                         [2016,2017,2018,2019,2021,2022,2023,2024,2025])
        pending=[x for x in catalog.get("pending_events",[]) if x["year"]==2026]
        published=[x for x in catalog.get("published_events",[]) if x["year"]==2026]
        self.assertEqual(len(pending)+len(published),1)
        event=(pending+published)[0]
        self.assertEqual(event["event_id"],82600)
        self.assertEqual(event["date"],"2026-11-07")
        self.assertEqual(event["url"],"https://live.eqtiming.com/82600")
        if pending:
            self.assertTrue(event["requires_private_registry_review"])
            self.assertEqual(event["publication_status"],"NOT_APPROVED")
        else:
            self.assertIn(event["publication_status"],
                          ("SOURCE_AND_PRIVACY_QA_PASSED_PENDING_PR","APPROVED_AND_PUBLISHED"))
            self.assertEqual(len(event["source_event_sha256"]),64)

    def test_2026_is_all_or_nothing_and_has_source_fingerprint(self):
        boot=json.loads((DATA/"bootstrap.json").read_text(encoding="utf-8"))
        catalog=json.loads((ROOT/"config/eqtiming-events.json").read_text(encoding="utf-8"))
        fp=json.loads((DATA/"source-fingerprints.json").read_text(encoding="utf-8"))
        current=[e for e in boot["editions"] if e["year"]==2026]
        files={f.name for f in (DATA/"races").glob("2026-*.json")}
        if catalog.get("published_events"):
            self.assertEqual({e["race_key"] for e in current},
                             {"2026-ultra85","2026-trail43","2026-trail22"})
            self.assertEqual(files,{"2026-ultra85.json","2026-trail43.json","2026-trail22.json"})
            self.assertEqual(fp["2026"]["event_id"],82600)
            self.assertEqual(fp["2026"]["event_json_sha256"],
                             catalog["published_events"][0]["source_event_sha256"])
        else:
            self.assertFalse(current)
            self.assertFalse(files)
            self.assertNotIn("2026",fp)

    def test_legacy_raw_capture_remains_disabled(self):
        workflow=(ROOT/".github/workflows/import-eqtiming.yml").read_text(encoding="utf-8")
        self.assertIn("if: ${{ false }}",workflow)
        self.assertIn("PRIVACY HOLD",workflow)


if __name__=="__main__":
    unittest.main()
