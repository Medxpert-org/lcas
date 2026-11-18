# -*- coding: utf-8 -*-
"""第三方可离线复跑的检验：契约不变式，不是回归快照。

跑法：python -m unittest discover tests -v
任一条失败即视为契约被破坏，不是"测试有点旧"。
"""
from __future__ import annotations

import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import judge  # noqa: E402

VERDICTS = {"IN_SCOPE", "NOT_REQUIRED", "OUT_OF_SCOPE", "UNCERTAIN", "BLOCK"}
ROUTES = {"PASS", "BLOCK", "REVIEW", "SIMPLIFIED"}
# SPEC §3：路由映射固定，不允许实现自行扩张
LEGAL_ROUTE = {"OUT_OF_SCOPE": "BLOCK", "BLOCK": "BLOCK", "UNCERTAIN": "REVIEW",
               "NOT_REQUIRED": "PASS", "IN_SCOPE": "PASS"}


def load_cases():
    with open(os.path.join(ROOT, "cases.json"), encoding="utf-8") as f:
        return json.load(f)["cases"]


class TestContract(unittest.TestCase):
    def test_verdict_and_route_are_declared(self):
        """任何输出都不得超出契约枚举。"""
        for case in load_cases():
            out = judge.judge(case)
            for jur, res in out["results"].items():
                with self.subTest(case=case["id"], jur=jur):
                    self.assertIn(res["verdict"], VERDICTS)
                    self.assertIn(res["route"], ROUTES)

    def test_route_mapping_holds(self):
        """verdict → route 必须按 SPEC 固定映射（SIMPLIFIED 仅中国侧简化通道例外）。"""
        for case in load_cases():
            out = judge.judge(case)
            for jur, res in out["results"].items():
                if res["route"] == "SIMPLIFIED":
                    continue
                with self.subTest(case=case["id"], jur=jur):
                    self.assertEqual(res["route"], LEGAL_ROUTE[res["verdict"]])

    def test_matches_expected(self):
        """55 个案例的期望结论必须全部命中。"""
        total = 0
        for case in load_cases():
            out = judge.judge(case)
            for jur, res in out["results"].items():
                exp = case.get("expected", {}).get(jur)
                if exp is None:
                    continue
                total += 1
                with self.subTest(case=case["id"], jur=jur):
                    self.assertEqual(res["verdict"], exp)
        self.assertGreaterEqual(total, 59, "案例覆盖不应少于 59 条判定")

    def test_no_silent_pass(self):
        """期望拦截/超范围的，绝不能被放行——安全方向错误必须为 0。"""
        for case in load_cases():
            out = judge.judge(case)
            for jur, res in out["results"].items():
                exp = case.get("expected", {}).get(jur)
                if exp in ("OUT_OF_SCOPE", "BLOCK"):
                    with self.subTest(case=case["id"], jur=jur):
                        self.assertNotEqual(res["route"], "PASS")

    def test_determinism(self):
        """同一输入两次运行逐字节相同（SPEC §4.1）。"""
        for case in load_cases():
            a = json.dumps(judge.judge(case), ensure_ascii=False, sort_keys=True)
            b = json.dumps(judge.judge(case), ensure_ascii=False, sort_keys=True)
            with self.subTest(case=case["id"]):
                self.assertEqual(a, b)

    def test_fail_closed_on_missing_device(self):
        """缺 device 不得抛异常、更不得放行（SPEC §2 / §4.4）。"""
        out = judge.judge({"id": "MISS-1", "change": {"significant": True}, "jurisdictions": ["US"]})
        self.assertEqual(out["results"]["US"]["verdict"], "UNCERTAIN")
        self.assertEqual(out["results"]["US"]["route"], "REVIEW")
        self.assertEqual(out["results"]["US"]["findings"][0]["rule_id"], "INPUT-MISSING")

    def test_fail_closed_on_missing_change(self):
        out = judge.judge({"id": "MISS-2", "device": {"has_pccp": True}, "jurisdictions": ["US", "EU"]})
        for jur in ("US", "EU"):
            with self.subTest(jur=jur):
                self.assertEqual(out["results"][jur]["verdict"], "UNCERTAIN")

    def test_every_finding_is_traceable(self):
        """每条 finding 必须带规则 id 与条文出处（SPEC §4.3）。"""
        for case in load_cases():
            out = judge.judge(case)
            for jur, res in out["results"].items():
                for f in res["findings"]:
                    with self.subTest(case=case["id"], jur=jur, rule=f.get("rule_id")):
                        self.assertTrue(f.get("rule_id"))
                        self.assertTrue(f.get("article"), "缺条文出处即不可追溯")


if __name__ == "__main__":
    unittest.main()
