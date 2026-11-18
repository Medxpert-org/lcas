#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_n90.py —— N90 投影的不变式测试。

要点：投影层不许偷偷补齐、不许改变裁决、不许把未登记规则静默吞掉。
"""
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import n90                      # noqa: E402
import judge                    # noqa: E402
import domains                  # noqa: E402


def all_rule_ids():
    ids = [r["id"] for r in judge.RULES]
    for rs in domains.DOMAIN_RULES.values():
        ids += [r["id"] for r in rs]
    return ids


class N90Mapping(unittest.TestCase):
    def test_every_rule_is_mapped(self):
        missing = [i for i in all_rule_ids() if i not in n90.MAPPING]
        self.assertEqual(missing, [], f"未登记到 N90 映射的规则: {missing}")

    def test_mapping_has_no_orphans(self):
        extra = [i for i in n90.MAPPING if i not in all_rule_ids()]
        self.assertEqual(extra, [], f"映射表里有不存在的规则: {extra}")

    def test_all_elements_have_rules(self):
        elems = {e for e, _ in n90.MAPPING.values()}
        self.assertEqual(elems, set(n90.ELEMENTS), "三要素未全部覆盖")

    def test_all_principles_have_rules(self):
        prs = {p for _, ps in n90.MAPPING.values() for p in ps}
        self.assertEqual(prs, set(n90.PRINCIPLES), "五原则未全部覆盖")


class N90View(unittest.TestCase):
    def _case(self, **kw):
        base = {"id": "T-1", "jurisdictions": ["US"],
                "device": {"name": "demo", "has_pccp": True, "pccp_scope_types": ["retrain"]},
                "change": {"type": "retrain", "description": "retrain on new data",
                           "validation_performed": False, "acceptance_met": False}}
        base["device"].update(kw.pop("device", {}))
        base["change"].update(kw.pop("change", {}))
        base.update(kw)
        return base

    def test_verdict_unchanged(self):
        case = self._case()
        plain = judge.judge(case)
        withn = n90.judge_with_n90(case)
        for jur in plain["results"]:
            self.assertEqual(plain["results"][jur]["verdict"], withn["results"][jur]["verdict"])
            self.assertEqual(plain["results"][jur]["route"], withn["results"][jur]["route"])

    def test_findings_land_in_elements(self):
        out = n90.judge_with_n90(self._case())
        plan_ids = [x["rule_id"] for x in out["n90"]["elements"]["plan"]]
        self.assertIn("US-PCCP-R4", plan_ids, "验证未完成应落在变更计划要素")

    def test_empty_element_is_gap_not_silence(self):
        case = self._case(jurisdictions=["CN"],
                          device={"has_pccp": False}, change={"type": "ui", "minor": True})
        out = n90.judge_with_n90(case)
        for e in n90.ELEMENTS:
            if not out["n90"]["elements"][e]:
                gaps = [g for g in out["n90"]["gaps"] if g.get("element") == e]
                self.assertTrue(gaps, f"{e} 为空时必须记 gap")

    def test_unmapped_rule_is_reported(self):
        out = {"results": {"US": {"findings": [{"rule_id": "XX-NEW-RULE", "effect": "BLOCK"}]}}}
        view = n90.n90_view(out)
        self.assertTrue(view["unmapped"], "未登记规则必须被报出，不得静默归类")


if __name__ == "__main__":
    unittest.main(verbosity=2)
