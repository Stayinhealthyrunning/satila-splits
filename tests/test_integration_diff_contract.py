#!/usr/bin/env python3
from __future__ import annotations
import json,tempfile,unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from audit_integration_diff import compare,surface

def write(root,rel,obj):
    p=Path(root)/rel;p.parent.mkdir(parents=True,exist_ok=True)
    if isinstance(obj,(dict,list)):p.write_text(json.dumps(obj,sort_keys=True),encoding="utf-8")
    else:p.write_text(str(obj),encoding="utf-8")

class IntegrationDiffContract(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.a=self.root/"a";self.b=self.root/"b"
        for r in (self.a,self.b):
            write(r,"docs/data/bootstrap.json",{"x":1})
            write(r,"docs/data/coverage.json",{"x":1})
            write(r,"docs/data/route-inventory.json",[{"family":"trail43"}])
            write(r,"docs/data/source-fingerprints.json",{"2025":{"event_id":1}})
            write(r,"docs/data/races/2025-trail43.json",{"race_key":"2025-trail43","results":[]})
            write(r,"docs/data/routes/trail43-2025-2026.json",{"family":"trail43","points":[[0,57,12,10]]})
            write(r,"config/eqtiming-events.json",{"events":[{"year":2025}]})
            write(r,"config/course-versions.json",{"version":1})
            write(r,"docs/assets/app.js","console.log('frontend')")

    def tearDown(self):self.tmp.cleanup()

    def test_frontend_only_change_is_allowed(self):
        write(self.b,"docs/assets/app.js","console.log('changed')")
        self.assertTrue(compare(self.a,self.b)["pass"])

    def test_race_bundle_change_is_caught(self):
        write(self.b,"docs/data/races/2025-trail43.json",{"race_key":"2025-trail43","results":[1]})
        result=compare(self.a,self.b)
        self.assertFalse(result["pass"])
        self.assertEqual(result["changed"],["docs/data/races/2025-trail43.json"])

    def test_route_change_is_caught(self):
        write(self.b,"docs/data/routes/trail43-2025-2026.json",{"family":"trail43","points":[[0,57.1,12,10]]})
        self.assertIn("docs/data/routes/trail43-2025-2026.json",compare(self.a,self.b)["changed"])

    def test_missing_or_extra_source_file_is_caught(self):
        (self.b/"docs/data/source-fingerprints.json").unlink()
        result=compare(self.a,self.b)
        self.assertIn("docs/data/source-fingerprints.json",result["missing"])
        write(self.b,"docs/data/races/2024-trail43.json",{"race_key":"2024-trail43"})
        result=compare(self.a,self.b)
        self.assertIn("docs/data/races/2024-trail43.json",result["extra"])

    def test_current_repository_surface_is_nontrivial(self):
        current=surface(ROOT)
        self.assertGreaterEqual(len(current),38)
        self.assertIn("docs/data/bootstrap.json",current)
        self.assertEqual(len([k for k in current if k.startswith("docs/data/races/")]),27)
        self.assertEqual(len([k for k in current if k.startswith("docs/data/routes/")]),5)

if __name__=="__main__":
    unittest.main(verbosity=2)
