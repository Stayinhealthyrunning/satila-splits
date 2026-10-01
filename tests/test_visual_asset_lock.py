#!/usr/bin/env python3
"""Lock the project-owner-approved Hero and design-reference binary assets."""
from __future__ import annotations
import hashlib,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LOCKS={
 "docs/assets/hero.webp":{
   "size":293818,
   "git_blob_sha1":"419ed7b410b497bdef0a29a9075555af2b1913f4",
 },
 "docs/assets/design-reference.webp":{
   "size":138976,
   "git_blob_sha1":"6c6aa3109638b86b35661773d4c05102eaac0b65",
 },
}
def git_blob_sha(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

class ApprovedVisualAssetLock(unittest.TestCase):
    def test_approved_visual_assets_are_byte_identical(self):
        for rel,lock in LOCKS.items():
            p=ROOT/rel
            self.assertTrue(p.is_file(),rel)
            raw=p.read_bytes()
            self.assertEqual(len(raw),lock["size"],rel)
            self.assertEqual(git_blob_sha(raw),lock["git_blob_sha1"],rel)

if __name__=="__main__":
    unittest.main(verbosity=2)
