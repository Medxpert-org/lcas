#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_pccp_field_audit.py —— 字段审计记录必须可核对、且不许被悄悄改成"能用"。

守三条：
1. 每条记录都有 510(k) 号、字段值、来源 URL；
2. 矛盾记录必须保留 `CONTRADICTION` 标记，不得被抹平；
3. 审计的 `do_not_claim` 必须存在，防止后续有人拿该字段算比例。
"""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
F = ROOT / "data" / "pccp_field_audit.json"


@unittest.skipUnless(F.exists(), "未检出审计记录")
class FieldAudit(unittest.TestCase):
    def setUp(self):
        self.d = json.loads(F.read_text(encoding="utf-8"))

    def test_records_have_sources(self):
        for r in self.d["records"]:
            for k in ("k_number", "field_value", "field_source"):
                self.assertIn(k, r)
            self.assertIn(r["field_value"], ("Yes", "No"))

    def test_contradiction_is_preserved(self):
        bad = [r for r in self.d["records"] if r["agreement"] == "CONTRADICTION"]
        self.assertGreaterEqual(len(bad), 1, "矛盾记录被抹掉了——这正是审计的价值")
        for r in bad:
            self.assertIn("summary_evidence", r)

    def test_forbids_using_field_for_rates(self):
        st = self.d["finding"]["statement"]
        self.assertIn("偏低", st)
        self.assertIn("不得用该字段计算 PCCP 采用率", self.d["finding"]["do_not_claim"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
