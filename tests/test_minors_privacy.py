"""Publication regression: minors must never appear in identifying race rows."""
from __future__ import annotations
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class MinorPrivacyTest(unittest.TestCase):
    def test_public_race_data_has_no_identifiable_minors(self):
        bundles=list((ROOT/'docs/data/races').glob('*.json'))
        self.assertEqual(len(bundles),27)
        for path in bundles:
            doc=json.loads(path.read_text(encoding='utf-8'))
            result_ids={r['id'] for r in doc['results']}
            for r in doc['results']:
                age=r.get('age')
                self.assertFalse(type(age) is int and 0<=age<18,
                    f'Unprotected under-18 age in {path.name}')
                self.assertNotEqual(r.get('name'),'Anonym löpare',
                    f'Pseudonymous individual row must be removed from {path.name}')
            for split in doc['splits']:
                self.assertIn(split['result_id'],result_ids,path.name)

if __name__=='__main__':unittest.main()
