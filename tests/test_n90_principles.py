#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_n90_principles.py —— 五原则材料检查的不变式。

守三条：每原则都有字段；缺字段必须 MISSING（不被其他原则带过）；齐备也不等于合规（meta 必须声明）。
"""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import n90_principles as np90   # noqa: E402


def full_case():
    return {
        "change": {"description": "retrain on new data", "rationale": "data expansion",
                   "boundary_statement": "params only, architecture fixed",
                   "risk_analysis": "risk unchanged", "verification_evidence": "bench 59/59"},
        "device": {"postmarket_plan": "quarterly drift review"},
    }


class Principles(unittest.TestCase):
    def test_every_principle_has_fields(self):
        self.assertEqual(set(np90.PRINCIPLE_FIELDS), set(np90.check_principles({}).keys()) - {"_meta"})

    def test_all_present(self):
        v = np90.check_principles(full_case())
        self.assertTrue(np90.summary(v)["complete_declared"])

    def test_missing_is_per_principle(self):
        c = full_case()
        c["device"].pop("postmarket_plan")
        v = np90.check_principles(c)
        self.assertEqual(v["tpl"]["status"], "MISSING")
        self.assertEqual(v["risk_based"]["status"], "PASS", "其他原则不应连带变 MISSING")
        self.assertEqual(np90.summary(v)["missing_principles"], ["tpl"]); self.assertEqual(np90.summary(v)["derived_principles"], [])

    def test_meta_denies_compliance(self):
        v = np90.check_principles(full_case())
        self.assertTrue(v["_meta"]["not_a_verdict"])
        self.assertEqual(v["_meta"]["kind"], "material_completeness")


if __name__ == "__main__":
    unittest.main(verbosity=2)
