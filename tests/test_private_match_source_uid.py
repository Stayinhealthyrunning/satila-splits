"""2026 privacy collision matching must be identity-aware and not leak extra keys."""
from __future__ import annotations
import base64
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from build_satila import private_match_record, strictly_suppressed_public_result
from privacy import load_rules, name_fingerprint, record_is_suppressed

class PrivateMatchIdentifiersTests(unittest.TestCase):
    def test_source_ids_are_transient_and_match_approved_uid_only(self):
        row={"id":"eq-2026-12-101","source_uid":101,"name":"Fictional Protected Runner",
             "bib":"101","age":35}
        old=dict(row)
        approved=private_match_record(row,{"UID":2101},101)
        other=private_match_record(row,{"UID":2102},102)
        self.assertEqual(row,old)
        self.assertEqual(approved["source_result_id"],"101")
        self.assertEqual(approved["public_contestant_uid"],"2101")
        self.assertNotIn("source_result_id",row)
        registry={"schema_version":2,"entries":[{
            "action":"remove_result","scopes":["2026-ultra85"],
            "require_review_for_new_matches":True,
            "match":{"normalized_name_sha256":name_fingerprint(row["name"])},
            "approved_matches":[{"scope":"2026-ultra85",
                                  "identifiers":{"source_result_id":"101"}}]}]}
        with patch.dict(os.environ,{
            "LOPPANALYS_PRIVACY_REGISTRY_B64":
                base64.b64encode(json.dumps(registry).encode()).decode(),
            "LOPPANALYS_PRIVACY_REGISTRY_PATH":"",
        }):
            rules=load_rules(ROOT/"config/privacy-suppressions.json",require_private=True)
            self.assertTrue(record_is_suppressed(approved,rules,scope="2026-ultra85"))
            with self.assertRaisesRegex(RuntimeError,"manual review"):
                record_is_suppressed(other,rules,scope="2026-ultra85")
    def test_ambiguous_protected_name_is_withheld_in_2026(self):
        row={"name":"Fictional Protected Runner","source_result_id":"555","age":35}
        reg={"schema_version":2,"entries":[{
            "action":"remove_result","scopes":["2026-ultra85"],
            "require_review_for_new_matches":True,
            "match":{"normalized_name_sha256":name_fingerprint(row["name"])},
            "approved_matches":[]} ]}
        with patch.dict(os.environ,{"LOPPANALYS_PRIVACY_REGISTRY_B64":
                base64.b64encode(json.dumps(reg).encode()).decode(),
                "LOPPANALYS_PRIVACY_REGISTRY_PATH":""}):
            rules=load_rules(ROOT/"config/privacy-suppressions.json",require_private=True)
            self.assertTrue(strictly_suppressed_public_result(
                row,rules,scope="2026-ultra85",year=2026))
            with self.assertRaisesRegex(RuntimeError,"manual review"):
                strictly_suppressed_public_result(
                    row,rules,scope="2025-ultra85",year=2025)

    def test_missing_contestant_uid_is_not_made_up(self):
        row={"name":"Fictional Runner","age":30}
        derived=private_match_record(row,{},5)
        self.assertEqual(derived["source_result_id"],"5")
        self.assertNotIn("public_contestant_uid",derived)

if __name__=="__main__":
    unittest.main()
