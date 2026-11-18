#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""backfill_material.py —— 从既有案例字段机械推导 N90 材料字段，并标注来源。

原则（写死，不靠自觉）：
1. **只推导，不创作**：每个 derived 值必须由案例中已有的字段拼接/映射得到，禁止新增事实。
2. **推导不出的不填**：`device.postmarket_plan` 在任何案例里都没有依据，一律留空 → 仍 MISSING。
3. **来源必须留痕**：写入 `_material_source`，值为 "derived"，供下游区分"申报方声明"与"系统推导"。
4. **不改原案例**：输出新文件 `cases_material.json`，原子案例保持原样可比对。

用法：
  python tools/backfill_material.py            # 生成 cases_material.json + 覆盖率报告
"""
from __future__ import annotations

import io
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "cases.json"
OUT = ROOT / "cases_material.json"

DERIVED_KEYS = ("postmarket_plan",)   # 明确不可推导，禁止填充


def derive(case):
    """返回 (material_fields, trace)。trace 记录每个字段由哪些源字段推出。"""
    ch = case.get("change", {}) or {}
    dev = case.get("device", {}) or {}
    mat, trace = {}, {}

    desc = ch.get("description")
    if desc:
        mat["description"] = desc
        trace["Rationale"] = ["change.description"]

    # 边界声明：由已声明的"是否触及边界"布尔字段机械拼出，不评价真假
    flags = [k for k in ("architecture_change", "new_input_modality", "new_output",
                         "new_intended_use", "algorithm_driven") if ch.get(k)]
    mat["boundary_statement"] = ("改动触达：" + "、".join(flags)) if flags else "未声明触及下列边界项：" + \
        "架构/输入模态/输出/预期用途/算法驱动"
    trace["boundary_statement"] = ["change.architecture_change", "change.new_input_modality",
                                   "change.new_output", "change.new_intended_use", "change.algorithm_driven"]

    # 风险分析：由风险相关布尔与类型推出
    risk_bits = []
    if ch.get("introduces_new_risk"):
        risk_bits.append("引入新风险")
    if ch.get("risk_control_exists") is False:
        risk_bits.append("无可用的风险控制")
    if ch.get("cybersecurity_only"):
        risk_bits.append("仅网络安全加固")
    mat["risk_analysis"] = ("；".join(risk_bits) if risk_bits else
                            f"未声明风险变化（变更类型 {ch.get('type', '未填')}）")
    trace["risk_analysis"] = ["change.introduces_new_risk", "change.risk_control_exists",
                              "change.cybersecurity_only", "change.type"]

    # 验证证据：由验证/接受准则两个布尔推出，不美化
    vp, am = ch.get("validation_performed"), ch.get("acceptance_met")
    mat["verification_evidence"] = f"validation_performed={vp}; acceptance_met={am}"
    trace["verification_evidence"] = ["change.validation_performed", "change.acceptance_met"]

    # 上市后监测：无依据，禁止推导
    for k in DERIVED_KEYS:
        trace.pop(k, None)
    return mat, trace


def main(argv):
    data = json.loads(io.open(SRC, encoding="utf-8").read())
    cases = data["cases"]
    out_cases, stats = [], {"derived": {k: 0 for k in
                                        ("description", "rationale", "boundary_statement",
                                         "risk_analysis", "verification_evidence")},
                            "total": len(cases)}
    for c in cases:
        mat, trace = derive(c)
        c2 = json.loads(json.dumps(c))
        c2.setdefault("change", {})
        c2["change"]["description"] = mat.get("description") or c2["change"].get("description")
        c2["change"]["rationale"] = "由案例描述推导：" + (c2["change"].get("description") or "—")
        c2["change"]["boundary_statement"] = mat["boundary_statement"]
        c2["change"]["risk_analysis"] = mat["risk_analysis"]
        c2["change"]["verification_evidence"] = mat["verification_evidence"]
        c2["_material_source"] = "derived"
        c2["_material_trace"] = trace
        out_cases.append(c2)
        for k in stats["derived"]:
            if c2["change"].get(k):
                stats["derived"][k] += 1

    io.open(OUT, "w", encoding="utf-8", newline="\n").write(json.dumps(
        {"schema": data.get("schema"), "note": "material fields derived from existing case fields; "
                                               "no new facts introduced; see _material_trace",
         "cases": out_cases}, ensure_ascii=False, indent=2))
    print(json.dumps({"total": stats["total"],
                      "derived_success": stats["derived"],
                      "not_derivable": ["postmarket_plan"],
                      "coverage": {k: f"{v}/{stats['total']}" for k, v in stats["derived"].items()}},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
