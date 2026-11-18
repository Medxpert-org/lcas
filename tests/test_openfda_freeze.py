#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_openfda_freeze.py —— 外部语料必须可离线核验（不联网也能证明没被改）。

守两条：
1. 冻结文件与 manifest 的 sha256 一致；
2. 记录数一致。
改文件不改 manifest，或反之，都会红——这是"外部记录"能被第三方复核的最低门槛。
"""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "openfda_510k_software.json"
MAN = ROOT / "data" / "openfda_510k_software.manifest.json"


@unittest.skipUnless(DATA.exists() and MAN.exists(), "未检出冻结语料")
class FreezeIntegrity(unittest.TestCase):
    def test_hash_matches(self):
        import hashlib
        d = json.loads(DATA.read_text(encoding="utf-8"))
        m = json.loads(MAN.read_text(encoding="utf-8"))
        raw = json.dumps(d["records"], ensure_ascii=False, sort_keys=True, indent=2)
        got = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        self.assertEqual(got, m["sha256"], "冻结语料与 manifest 哈希不一致，可能被改动过")
        self.assertEqual(len(d["records"]), m["record_count"])

    def test_manifest_declares_provenance(self):
        m = json.loads(MAN.read_text(encoding="utf-8"))
        for k in ("source", "query", "fetched_at_utc"):
            self.assertIn(k, m)
        self.assertEqual(m["source"], "https://api.fda.gov/device/510k.json")


if __name__ == "__main__":
    unittest.main(verbosity=2)
