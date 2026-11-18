#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""n90.py —— 把 judge() 的五档裁决，投影成 IMDRF N90 的三要素 / 五原则视图。

为什么要有这层：`judge()` 回答"这次改动要不要报"，但监管读者问的是另一组问题——
描述变更写清了吗？计划里验证与接受准则齐了吗？影响评估做了吗？三要素是 IMDRF
N90 FINAL:2026 规定的 PCCP 结构与审评抓手（见 SPEC §6）。

本模块**只做投影，不改裁决**：verdict / route / findings 原样保留，附加
`n90` 字段。投影不出来的情形必须显式记 gap，不得默认补齐。

用法：
  from n90 import n90_view
  out = judge(case); out["n90"] = n90_view(out)

  python n90.py case.json      # 打印带 n90 视图的完整输出
"""
from __future__ import annotations

import json
import sys

ELEMENTS = ("description", "plan", "impact")
ELEMENT_ZH = {
    "description": "描述变更（Description of Changes）",
    "plan": "变更计划（Change Plan）",
    "impact": "影响评估（Impact Assessment）",
}
PRINCIPLES = ("focused_and_bounded", "risk_based", "evidence_based", "transparent", "tpl")
PRINCIPLE_ZH = {
    "focused_and_bounded": "聚焦且有边界",
    "risk_based": "基于风险",
    "evidence_based": "基于证据",
    "transparent": "透明",
    "tpl": "全生命周期视角",
}

# rule_id -> (要素, 原则列表)
# 40 条规则逐条登记；新增规则若未登记，n90_view 会报 unmapped，而不是静默归类。
MAPPING = {
    # ---- 描述变更：改的是什么、有没有越过声明边界
    "US-807-81-A3": ("description", ["focused_and_bounded"]),
    "US-PCCP-R1": ("description", ["focused_and_bounded", "transparent"]),
    "US-PCCP-R2": ("description", ["focused_and_bounded"]),
    "US-PCCP-R3": ("description", ["focused_and_bounded"]),
    "CN-AI-LOCK": ("description", ["focused_and_bounded"]),
    "CN-ALG-DRIVEN": ("description", ["focused_and_bounded", "risk_based"]),
    "CN-INTENDED-USE": ("description", ["focused_and_bounded"]),
    "CN-ARCH-CHANGE": ("description", ["focused_and_bounded"]),
    "CN-PERF-SIMPLIFY": ("description", ["evidence_based"]),
    "EU-INTENDED-USE": ("description", ["focused_and_bounded"]),
    "EU-CLASS-CHANGE": ("description", ["focused_and_bounded", "risk_based"]),
    "EU-43-4-SUBSTANTIAL": ("description", ["focused_and_bounded"]),
    "DR-INTENDED-USE": ("description", ["focused_and_bounded"]),
    "DR-CN-INTENDED-USE": ("description", ["focused_and_bounded"]),
    "DR-PACMP-OUT": ("description", ["focused_and_bounded"]),
    "DR-PACMP-ABSENT": ("description", ["focused_and_bounded"]),
    "DR-CN-SUPPL": ("description", ["focused_and_bounded"]),
    "AU-INTENDED-USE": ("description", ["focused_and_bounded", "risk_based"]),
    "AU-INTENDED-USE-REVIEW": ("description", ["focused_and_bounded"]),
    "AU-SAFETY": ("description", ["focused_and_bounded", "risk_based"]),

    # ---- 变更计划：怎么实施、验证与接受准则、状态可追溯
    "US-PCCP-R4": ("plan", ["evidence_based", "transparent"]),
    "US-PCCP-OK": ("plan", ["evidence_based", "transparent"]),
    "DR-COND-MET": ("plan", ["evidence_based"]),
    "DR-PACMP-IN": ("plan", ["transparent", "evidence_based"]),
    "DR-CN-PACMP": ("plan", ["transparent"]),
    "AU-RXSWIN": ("plan", ["transparent"]),

    # ---- 影响评估：风险、性能差异、网络安全、轻微更新的判据
    "US-SW-Q1": ("impact", ["risk_based"]),
    "US-SW-Q2": ("impact", ["risk_based"]),
    "US-SW-Q3": ("impact", ["risk_based"]),
    "CN-DATA-DRIVEN-DIFF": ("impact", ["risk_based", "evidence_based"]),
    "CN-DATA-DRIVEN-OK": ("impact", ["evidence_based"]),
    "CN-NO-PCCP": ("impact", ["focused_and_bounded", "transparent"]),
    "CN-MINOR": ("impact", ["tpl", "risk_based"]),
    "EU-43-4-PREDET": ("impact", ["transparent", "tpl"]),
    "EU-MDR-NB": ("impact", ["risk_based", "evidence_based"]),
    "EU-CYBER-MINOR": ("impact", ["tpl", "risk_based"]),
    "EU-PERF-TUNE": ("impact", ["evidence_based", "tpl"]),
    "DR-VAR-MAJOR": ("impact", ["risk_based"]),
    "AU-SUMS-OK": ("impact", ["tpl", "transparent"]),
    "AU-SUMS-OUT": ("impact", ["risk_based", "transparent"]),
}

# 合法但不在 N90 三要素内的规则（输入不全等），投影时单独列出
NON_N90 = {"GEN-INSUFFICIENT", "INPUT-MISSING"}


def n90_view(out):
    """在 judge() 输出上附加 n90 视图。"""
    view = {"elements": {e: [] for e in ELEMENTS},
            "principles": {p: [] for p in PRINCIPLES},
            "gaps": [], "unmapped": [], "note": ""}

    per_jur = {}
    for jur, r in out.get("results", {}).items():
        ids = []
        for f in r.get("findings", []):
            rid = f.get("rule_id", "")
            ids.append(rid)
            if rid in NON_N90:
                continue
            if rid not in MAPPING:
                view["unmapped"].append({"jurisdiction": jur, "rule_id": rid})
                continue
            elem, prs = MAPPING[rid]
            view["elements"][elem].append({"jurisdiction": jur, "rule_id": rid,
                                           "effect": f.get("effect"),
                                           "reason": f.get("reason") or f.get("desc", "")})
            for p in prs:
                view["principles"][p].append({"jurisdiction": jur, "rule_id": rid})
        per_jur[jur] = ids

    # 覆盖缺口：没有任何规则落到的要素/原则，必须显式记 gap
    for e in ELEMENTS:
        if not view["elements"][e]:
            view["gaps"].append({"element": e, "why": "本次裁决未触发该要素下的任何规则",
                                 "action": "不视为该要素已完成评估；如需覆盖，须人工补材料"})
    for p in PRINCIPLES:
        if not view["principles"][p]:
            view["gaps"].append({"principle": p, "why": "本次裁决无规则落在该原则",
                                 "action": "不得声称本次判定完整符合 N90 五原则"})

    view["note"] = ("三要素是材料结构，不是裁决结果；空要素表示'这次没有规则触发它'，"
                    "不等于'该要素不适用'。本视图不改变 verdict 与 route。")
    return view


def judge_with_n90(case):
    from judge import judge
    out = judge(case)
    out["n90"] = n90_view(out)
    try:
        from n90_principles import check_principles
        out["n90_principles"] = check_principles(case)
    except ImportError:
        out["n90_principles"] = {"_meta": {"kind": "material_completeness", "not_a_verdict": True,
                                          "note": "未安装 n90_principles 模块，本次不检查材料完备度"}}
    return out


def main(argv):
    if len(argv) < 2:
        print("usage: python n90.py <case.json | ->"); return 2
    src = argv[1]
    case = json.loads(sys.stdin.read()) if src == "-" else json.loads(open(src, encoding="utf-8").read())
    print(json.dumps(judge_with_n90(case), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
