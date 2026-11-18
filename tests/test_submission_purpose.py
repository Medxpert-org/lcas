#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_submission_purpose.py —— "需提交"与"已提交获授权"不得混为一谈。

真实材料（K252844）暴露的问题：判定器回答的是"该改动是否需要新提交"，
但该提交本身的目的就是取得 PCCP 授权。答案 OUT_OF_SCOPE（=需提交）与
"已提交并获授权"是两个命题，必须靠语境标注区分，且**标注不得改写裁决**。
"""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import judge  # noqa: E402


def base(purpose=None):
    c = {"id": "T", "jurisdictions": ["US"],
         "device": {"name": "d", "has_pccp": True, "pccp_scope_types": ["algorithm_update"]},
         "change": {"type": "security_patch", "description": "third-party lib patch",
                    "cybersecurity_only": True, "significant": False,
                    "validation_performed": True, "acceptance_met": True}}
    if purpose:
        c["submission_purpose"] = purpose
    return c


class SubmissionPurpose(unittest.TestCase):
    def test_verdict_is_unchanged_by_annotation(self):
        plain = judge.judge_one(base(), "US")
        annotated = judge.judge_one(base("pccp_authorization"), "US")
        self.assertEqual(plain["verdict"], annotated["verdict"])
        self.assertEqual(plain["route"], annotated["route"])
        self.assertIsNone(plain["context"])
        self.assertIn("不判断", annotated["context"])

    def test_annotation_is_not_a_verdict_change(self):
        out = judge.judge_one(base("pccp_authorization"), "US")
        for k in ("verdict", "route", "findings"):
            self.assertIn(k, out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
