#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_pccp_boundary.py —— 边界授权必须逐项判断（真实材料回放推出的修正）。

两个方向都要守：
  A. 授权了架构修改 + 辅助输入 → 不得判越界（K252041 真实案例）；
  B. 只授权重训却改了输入模态 → 必须判越界（US-02 合成案例）。
用"触达即越界"会误杀 A，用"类型在范围内即放行"会漏放 B。
"""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import judge  # noqa: E402


def case(authorized, **change):
    c = {"id": "T", "jurisdictions": ["US"],
         "device": {"name": "d", "has_pccp": True,
                    "pccp_scope_types": ["model_retrain", "model_architecture"]},
         "change": {"type": "model_retrain", "description": "x",
                    "validation_performed": True, "acceptance_met": True}}
    if authorized is not None:
        c["device"]["pccp_authorized"] = authorized
    c["change"].update(change)
    return c


class BoundaryAuthorization(unittest.TestCase):
    def test_authorized_boundary_is_in_scope(self):
        c = case(["architecture_change", "new_input_modality"],
                 architecture_change=True, new_input_modality=True)
        self.assertEqual(judge.judge_one(c, "US")["verdict"], "IN_SCOPE")

    def test_unlisted_boundary_stays_out_of_scope(self):
        c = case(["model_retrain"], new_input_modality=True)   # 声明只含重训
        self.assertEqual(judge.judge_one(c, "US")["verdict"], "OUT_OF_SCOPE")
        ids = [f["rule_id"] for f in judge.judge_one(c, "US")["findings"]]
        self.assertIn("US-PCCP-R3", ids)

    def test_no_authorization_list_keeps_old_behaviour(self):
        c = case(None, architecture_change=True)
        self.assertEqual(judge.judge_one(c, "US")["verdict"], "OUT_OF_SCOPE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
