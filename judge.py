"""lgd-engine · PCCP / 变更判定器 v0.1

一句话：把"这次改动超没超出已批准范围"从人的判断，变成可复核的裁决。

设计约束（不是可选项）：
1. 只输出"决策建议"，不输出"合规结论"——法律责任在注册人。
2. 未知一律进人工（fail-closed），绝不静默放行。
3. 每条裁决必须带：rule_id + 法条锚 + 判定理由 + 置信度。
4. 同一变更可跨法域并判（US / CN / EU），差异单独说明。
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from domains import DOMAIN_RULES

VERDICT_ORDER = ["OUT_OF_SCOPE", "BLOCK", "UNCERTAIN", "NOT_REQUIRED", "IN_SCOPE"]

ROUTE = {
    "OUT_OF_SCOPE": "BLOCK",
    "BLOCK": "BLOCK",
    "UNCERTAIN": "REVIEW",
    "NOT_REQUIRED": "PASS",
    "IN_SCOPE": "PASS",
}


def _ch(c):
    return c["change"]


def _dv(c):
    return c["device"]


def _in_scope_type(c):
    types = _dv(c).get("pccp_scope_types") or []
    return _ch(c).get("type") in types


BOUNDARY_FLAGS = ("architecture_change", "new_input_modality", "new_output")


def _crossed_boundaries(c):
    """本次改动触达了哪些边界项（架构 / 输入模态 / 输出）。"""
    return [k for k in BOUNDARY_FLAGS if _ch(c).get(k)]


def _unauthorized_boundaries(c):
    """触达但**未被 PCCP 逐项授权**的边界项。

    2026-11-18 修正（真实材料回放发现误拦）：边界授权是逐项的——
    K252041 的 PCCP 明确授权"模型架构修改 + 辅助输入"，但 US-02 只授权"重训"却改了输入模态。
    因此不得用"触达即越界"，也不得用"类型在范围内即放行"，必须看 device.pccp_authorized。
    """
    authorized = set(_dv(c).get("pccp_authorized") or [])
    return [k for k in _crossed_boundaries(c) if k not in authorized]


# ---------------------------------------------------------------- 规则表
# effect: OUT_OF_SCOPE / BLOCK / NOT_REQUIRED / IN_SCOPE
RULES = [
    # ---------------- 美国：510(k) 变更判定 + PCCP
    dict(id="US-807-81-A3", jur="US", effect="OUT_OF_SCOPE",
         article="21 CFR 807.81(a)(3)",
         desc="预期用途发生重大改变 → 需新的上市前提交",
         test=lambda c: bool(_ch(c).get("new_intended_use"))),
    dict(id="US-PCCP-R1", jur="US", effect="OUT_OF_SCOPE",
         article="FDA PCCP Guidance §V Policy + 21 CFR 807.81(a)(3)",
         desc="无已授权 PCCP 而变更可能显著影响安全有效性 → 需提交",
         test=lambda c: (not _dv(c).get("has_pccp")) and bool(_ch(c).get("significant"))),
    dict(id="US-PCCP-R2", jur="US", effect="OUT_OF_SCOPE",
         article="FDA PCCP Guidance §VI Description of Modifications",
         desc="变更类型不在已授权 PCCP 的计划变更清单内 → 超范围",
         test=lambda c: bool(_dv(c).get("has_pccp")) and not _in_scope_type(c)),
    dict(id="US-PCCP-R3", jur="US", effect="OUT_OF_SCOPE",
         article="FDA PCCP Guidance §VI（范围界定）+ §VII",
         desc="触达未被 PCCP 逐项授权的边界项（架构/输入模态/输出）→ 越界",
         test=lambda c: bool(_dv(c).get("has_pccp")) and bool(_unauthorized_boundaries(c))),
    dict(id="US-PCCP-R4", jur="US", effect="BLOCK",
         article="FDA PCCP Guidance §VII Modification Protocol（预定义接受准则）",
         desc="落在 PCCP 范围内，但验证未完成或未达接受准则 → 不可实施，先补验证",
         test=lambda c: bool(_dv(c).get("has_pccp")) and _in_scope_type(c)
         and (not _ch(c).get("validation_performed") or not _ch(c).get("acceptance_met"))),
    dict(id="US-SW-Q1", jur="US", effect="NOT_REQUIRED",
         article="Deciding When to Submit a 510(k) for a Software Change, Q1",
         desc="仅为加强网络安全且不影响安全有效性 → 通常不需提交",
         test=lambda c: bool(_ch(c).get("cybersecurity_only")) and not _ch(c).get("significant")),
    dict(id="US-SW-Q2", jur="US", effect="NOT_REQUIRED",
         article="Deciding When to Submit a 510(k) for a Software Change, Q2",
         desc="仅为把系统恢复到规格内 → 通常不需提交",
         test=lambda c: bool(_ch(c).get("return_to_spec")) and not _ch(c).get("significant")),
    dict(id="US-SW-Q3", jur="US", effect="OUT_OF_SCOPE",
         article="Deciding When to Submit a 510(k) for a Software Change, Q3a/Q3b（新增或修改危险/风险控制）",
         desc="引入新风险或需新风险控制而未建立 → 需提交",
         test=lambda c: bool(_ch(c).get("introduces_new_risk")) and not _ch(c).get("risk_control_exists")),
    dict(id="US-PCCP-OK", jur="US", effect="IN_SCOPE",
         article="FDA PCCP Guidance §V（经授权 PCCP 内实施无需新提交）",
         desc="在已授权 PCCP 范围内且验证与接受准则均已满足 → 可依 PCCP 实施",
         test=lambda c: bool(_dv(c).get("has_pccp")) and _in_scope_type(c)
         and bool(_ch(c).get("validation_performed")) and bool(_ch(c).get("acceptance_met"))
         and not _unauthorized_boundaries(c)),

    # ---------------- 中国：算法锁定 + 重大/轻微软件更新
    dict(id="CN-AI-LOCK", jur="CN", effect="OUT_OF_SCOPE",
         article="人工智能医疗器械注册审查指导原则（算法锁定与自学习禁令）",
         desc="自学习/在线学习 → 违反算法锁定要求，必须变更注册",
         test=lambda c: bool(_ch(c).get("online_learning"))),
    dict(id="CN-ALG-DRIVEN", jur="CN", effect="OUT_OF_SCOPE",
         article="深度学习辅助决策医疗器械软件审评要点（二）重大软件更新",
         desc="算法驱动型更新（算法/结构/流程/框架/输入输出改变，或重新训练）→ 重大软件更新",
         test=lambda c: bool(_ch(c).get("algorithm_driven"))),
    dict(id="CN-DATA-DRIVEN-DIFF", jur="CN", effect="OUT_OF_SCOPE",
         article="同上：数据驱动型以性能评估结果是否具统计学显著差异为判据",
         desc="仅训练数据量增加，但性能评估出现显著差异 → 重大软件更新",
         test=lambda c: bool(_ch(c).get("data_driven")) and bool(_ch(c).get("perf_significant_diff"))),
    dict(id="CN-DATA-DRIVEN-OK", jur="CN", effect="NOT_REQUIRED",
         article="同上：数据驱动型性能无显著差异",
         desc="仅训练数据量增加且性能无统计学显著差异 → 体系内控制，不需变更注册",
         test=lambda c: bool(_ch(c).get("data_driven")) and not bool(_ch(c).get("perf_significant_diff"))
         and not bool(_ch(c).get("algorithm_driven"))),
    dict(id="CN-NO-PCCP", jur="CN", effect="OUT_OF_SCOPE",
         article="NMPA 现行体系：无预定变更（PCCP）通道",
         desc="NMPA 不接受「预定变更」式免责；影响安全有效性的更新一律走变更注册",
         test=lambda c: bool(_ch(c).get("significant")) or bool(_ch(c).get("unknown_pccp_claim"))),
    dict(id="CN-PERF-SIMPLIFY", jur="CN", effect="OUT_OF_SCOPE",
         article="国家药监局 2025 年第 63 号公告 · 四",
         desc="核心算法不变、仅算法性能优化 → 走简化变更注册（仍需申报，但不走完整路径）",
         test=lambda c: bool(_ch(c).get("core_algo_unchanged")) and bool(_ch(c).get("perf_optimization_only"))),
    dict(id="CN-INTENDED-USE", jur="CN", effect="OUT_OF_SCOPE",
         article="《医疗器械注册与备案管理办法》（市场监管总局令第 47 号，2021-10-01 施行）",
         desc="适用范围（预期用途）改变 → 须变更注册",
         test=lambda c: bool(_ch(c).get("new_intended_use"))),
    dict(id="CN-ARCH-CHANGE", jur="CN", effect="OUT_OF_SCOPE",
         article="深度学习辅助决策软件审评要点：算法结构/流程/输入输出改变属算法驱动型",
         desc="算法结构或输入输出改变（即使未标注 algorithm_driven）→ 重大软件更新",
         test=lambda c: bool(_ch(c).get("architecture_change"))
         or bool(_ch(c).get("new_input_modality")) or bool(_ch(c).get("new_output"))),
    dict(id="CN-MINOR", jur="CN", effect="NOT_REQUIRED",
         article="医疗器械软件注册审查指导原则（重大/轻微软件更新）",
         desc="轻微软件更新 → 质量管理体系控制，不需变更注册",
         test=lambda c: not any(bool(_ch(c).get(k)) for k in (
             "significant", "algorithm_driven", "online_learning", "perf_significant_diff",
             "new_intended_use", "architecture_change", "new_input_modality", "new_output"))),

    # ---------------- 欧盟：AI Act 第 43(4) 条
    dict(id="EU-43-4-PREDET", jur="EU", effect="NOT_REQUIRED",
         article="EU AI Act Art.43(4) + Annex IV point 2(f)",
         desc="变更在初次符合性评估时已预定并写入技术文档 → 不构成实质性修改",
         test=lambda c: bool(_ch(c).get("predetermined_documented")) and not bool(_ch(c).get("new_intended_use"))),
    dict(id="EU-43-4-SUBSTANTIAL", jur="EU", effect="OUT_OF_SCOPE",
         article="EU AI Act Art.43(4)",
         desc="构成实质性修改 → 须重做符合性评估",
         test=lambda c: not bool(_ch(c).get("predetermined_documented")) and bool(_ch(c).get("significant"))),
    dict(id="EU-MDR-NB", jur="EU", effect="OUT_OF_SCOPE",
         article="EU MDR Art.120 / 公告机构显著变更通知",
         desc="影响安全或性能的显著变更 → 需公告机构评估",
         test=lambda c: bool(_ch(c).get("significant")) and not bool(_ch(c).get("predetermined_documented"))),
    # ---- v0.2 补齐的 EU 覆盖（关闭 X-02 暴露的缺口）
    dict(id="EU-CYBER-MINOR", jur="EU", effect="NOT_REQUIRED",
         article="MDR Art.120 + MDCG 2019-16（网络安全要求）",
         desc="仅为网络安全加固、不改预期用途且不构成显著变更 → 制造商内部评估，不需公告机构",
         test=lambda c: bool(_ch(c).get("cybersecurity_only")) and not bool(_ch(c).get("significant"))),
    dict(id="EU-PERF-TUNE", jur="EU", effect="NOT_REQUIRED",
         article="MDR Art.52（符合性评估程序）",
         desc="核心算法不变、仅性能优化、预期用途不变且非显著变更 → 制造商内部评估",
         test=lambda c: bool(_ch(c).get("perf_optimization_only")) and bool(_ch(c).get("core_algo_unchanged"))
         and not bool(_ch(c).get("significant")) and not bool(_ch(c).get("new_intended_use"))),
    dict(id="EU-CLASS-CHANGE", jur="EU", effect="OUT_OF_SCOPE",
         article="MDR Annex VIII 分类规则；Art.52 符合性评估程序",
         desc="器械风险分类发生变化 → 须按新类别重新符合性评估",
         test=lambda c: bool(_ch(c).get("risk_class_change"))),
    dict(id="EU-INTENDED-USE", jur="EU", effect="OUT_OF_SCOPE",
         article="MDR Art.2(1) 预期用途；Annex VIII 分类",
         desc="预期用途改变 → 视为新器械，须重新进行符合性评估",
         test=lambda c: bool(_ch(c).get("new_intended_use"))),
]

JUR_BLOCK = {"EU": "EU-43-4-SUBSTANTIAL", "US": "US-PCCP-R1"}


def _fingerprint(rule):
    raw = f"{rule['id']}|{rule['article']}|{rule['effect']}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def judge_one(case, jur):
    # 行业规则库：默认医械，drug / auto 走 domains.py，互不串用
    domain = case.get("domain", "device")
    extra = DOMAIN_RULES.get(domain, [])
    all_rules = list(RULES) if domain == "device" else list(extra)
    findings = []
    for r in all_rules:
        if r["jur"] != jur:
            continue
        try:
            fired = bool(r["test"](case))
        except Exception:
            fired = False
        if fired:
            findings.append({
                "rule_id": r["id"],
                "article": r["article"],
                "effect": r["effect"],
                "reason": r["desc"],
                "fingerprint": _fingerprint(r),
            })

    # 信息不足 → 未决（fail-closed）
    if not _ch(case).get("description") and not findings:
        findings.append({"rule_id": "GEN-INSUFFICIENT", "article": "—",
                         "effect": "UNCERTAIN", "reason": "变更描述缺失，无法判定",
                         "fingerprint": "gen-insufficient"})

    effects = [f["effect"] for f in findings] or ["UNCERTAIN"]
    verdict = min(effects, key=VERDICT_ORDER.index)
    route = ROUTE[verdict]

    # 简化路径：中国侧"核心算法不变 + 性能优化"单独标注
    if any(f["rule_id"] == "CN-PERF-SIMPLIFY" for f in findings) and verdict == "OUT_OF_SCOPE":
        route = "SIMPLIFIED"

    # 置信度：硬裁决为高；依赖单一宽容条款为中；未决为低
    if verdict in ("OUT_OF_SCOPE", "BLOCK") and findings:
        conf = "high"
    elif verdict in ("NOT_REQUIRED", "IN_SCOPE") and findings:
        conf = "medium" if len(findings) == 1 else "high"
    else:
        conf = "low"

    # 语境标注（2026-11-18，真实材料回放推出）：本判定回答的是"这次改动是否需要新提交"。
    # 当提交本身以取得 PCCP 授权为目的（REAL-02 / K252844）时，OUT_OF_SCOPE 意为"需提交"，
    # 而"已提交并获授权"是另一个命题。标注不得改写裁决，只防止误读。
    context = None
    if case.get("submission_purpose") == "pccp_authorization":
        context = ("本次提交目的为取得 PCCP 授权；裁决只回答'该改动是否需要新提交'，"
                   "不判断'该 PCCP 是否已获授权'。")

    return {
        "jurisdiction": jur,
        "verdict": verdict,
        "route": route,
        "confidence": conf,
        "findings": findings,
        "context": context,
    }


REQUIRED_INPUT = ("device", "change", "jurisdictions")


def missing_input(case):
    """SPEC §2：缺必填字段必须 fail-closed，不得用默认值猜。"""
    return [k for k in REQUIRED_INPUT if not isinstance(case.get(k), (dict, list))]


def _fail_closed(case, missing):
    jur_list = case.get("jurisdictions") or ["US"]
    results = {}
    for jur in jur_list:
        results[jur] = {
            "jurisdiction": jur, "verdict": "UNCERTAIN", "route": "REVIEW", "confidence": "low",
            "findings": [{"rule_id": "INPUT-MISSING", "effect": "UNCERTAIN",
                          "article": "LCAS-0.1 §2（必填字段缺失 → 无法判定）",
                          "desc": "缺少必填输入：" + "、".join(missing)}],
        }
    return {
        "case_id": case.get("id"), "device": "", "results": results,
        "divergence": {"divergent": False, "note": "输入不全，未进入规则判定"},
        "disclaimer": "本输出为决策建议，非合规结论；采信与法律责任在注册人。",
    }


def judge(case):
    missing = missing_input(case)
    if missing:
        return _fail_closed(case, missing)
    res = {"case_id": case.get("id"), "device": _dv(case).get("name", ""),
           "results": {}}
    for jur in case.get("jurisdictions", []):
        res["results"][jur] = judge_one(case, jur)
    res["divergence"] = explain_divergence(res["results"])
    res["disclaimer"] = "本输出为决策建议，非合规结论；采信与法律责任在注册人。"
    return res


def explain_divergence(results):
    verdicts = {j: r["verdict"] for j, r in results.items()}
    if len(set(verdicts.values())) <= 1:
        return {"divergent": False, "note": "各法域结论一致"}
    causes = []
    gaps = [j for j, v in verdicts.items() if v == "UNCERTAIN"]
    if gaps:
        causes.append(f"{'/'.join(gaps)} 侧尚无该情形的判定规则，按 fail-closed 进人工（已知覆盖缺口）")
    rest = {j: v for j, v in verdicts.items() if j not in gaps}
    if len(set(rest.values())) > 1:
        causes.append("是否承认「预定变更」免责不同：US PCCP 与 EU Art.43(4) 承认，NMPA 不承认")
    return {"divergent": True, "verdicts": verdicts, "note": "；".join(causes) or "规则适用差异"}


def main(argv):
    if len(argv) < 2:
        print("usage: python judge.py <case.json | ->"); return 2
    src = argv[1]
    if src == "-":
        case = json.loads(sys.stdin.read())
    else:
        case = json.loads(Path(src).read_text(encoding="utf-8"))
    out = judge(case)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if all(r["route"] != "BLOCK" for r in out["results"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
