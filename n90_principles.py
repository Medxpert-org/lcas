#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""n90_principles.py —— 五原则的材料完备度检查（不是法规判定）。

为什么单独一层：`n90.py` 把**已判定的规则**投影成三要素，但投影不出来"材料本身是否齐"。
IMDRF N90 的五原则里，「透明」和「全生命周期视角」在规则表里没有独立落点（SPEC §9.3 已登记），
补规则要编法条锚，不能编。所以改为检查**申报材料是否具备该原则所需的字段**——
这是可验证的、不冒充法规判断的做法。

边界（三条，缺一即违约）：
1. 只回答"这份材料缺什么"，不回答"是否合规"。
2. 缺失即 MISSING，不因其他原则通过而略过。
3. 字段由申报方自填，系统不校验真伪（同 SPEC §9.1 声明的信任边界）。

用法：
  from n90_principles import check_principles
  check_principles(case)  ->  {"focused_and_bounded": {...}, ...} 每项 PASS/MISSING
"""
from __future__ import annotations

import json
import sys

# 原则 -> 需要的字段（字段名取自 change / device 两个块，用 "." 表示层级）
PRINCIPLE_FIELDS = {
    "focused_and_bounded": [
        ("change.boundary_statement", "变更边界声明（哪些改、哪些不改）"),
    ],
    "risk_based": [
        ("change.risk_analysis", "变更的风险分析"),
    ],
    "evidence_based": [
        ("change.verification_evidence", "验证/确认证据（含接受准则判定结果）"),
    ],
    "transparent": [
        ("change.description", "变更描述"),
        ("change.rationale", "变更理由（为什么要这样改）"),
    ],
    "tpl": [
        ("device.postmarket_plan", "上市后性能监测计划"),
    ],
}


def _get(case, path):
    cur = case
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def check_principles(case):
    out = {}
    missing_all = []
    provenance = case.get("_material_source")     # "derived" 时，值来自系统推导而非申报方声明
    for p, fields in PRINCIPLE_FIELDS.items():
        missing = []
        for path, label in fields:
            v = _get(case, path)
            if v in (None, "", [], {}):
                missing.append({"field": path, "label": label})
        if missing:
            status = "MISSING"
        elif provenance == "derived":
            status = "PASS_DERIVED"
        else:
            status = "PASS"
        out[p] = {"status": status, "missing": missing}
        missing_all += [{"principle": p, **m} for m in missing]

    out["_meta"] = {
        "kind": "material_completeness",
        "not_a_verdict": True,
        "note": ("本检查只看材料是否具备，不看内容是否正确；缺失不等于违规，齐备也不等于合规。"
                 "字段由申报方自填，系统不校验真伪。PASS_DERIVED 表示该字段由案例既有字段"
                 "机械推导（见 _material_trace），不是申报方声明。"),
        "provenance": provenance or "declared",
        "missing_total": len(missing_all),
    }
    return out


def summary(view):
    """给一行结论用：哪些原则缺材料；派生通过单独计数，不混进 PASS。"""
    bad = [p for p, v in view.items() if isinstance(v, dict) and v.get("status") == "MISSING"]
    derived = [p for p, v in view.items() if isinstance(v, dict) and v.get("status") == "PASS_DERIVED"]
    return {"missing_principles": bad, "derived_principles": derived,
            "complete_declared": not bad and not derived}


def main(argv):
    if len(argv) < 2:
        print("usage: python n90_principles.py <case.json | ->"); return 2
    case = json.loads(sys.stdin.read()) if argv[1] == "-" else json.loads(
        open(argv[1], encoding="utf-8").read())
    print(json.dumps(check_principles(case), ensure_ascii=False, indent=2))
    return 0 if not summary(check_principles(case))["complete"] == 1 else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
