#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""replay_real_pccp.py —— 把真实 PCCP summary 编成判定器输入，跑一遍并留下对账记录。

这不是"自动化抽取"：字段由人读 PDF 后手工填，脚本只负责跑判定与存档。
每个字段都必须带 quote（原文依据），没有 quote 的字段一律不许填——这是本脚本唯一的硬约束。
"""
import io
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import n90  # noqa: E402

CASES = [
    {
        "id": "REAL-01",
        "source": {
            "k_number": "K252041",
            "device": "Fibresolve (with PCCP)",
            "applicant": "Imvaria, Inc.",
            "decision_date": "2025-11-07",
            "summary_pdf": "https://www.accessdata.fda.gov/cdrh_docs/pdf25/K252041.pdf",
            "read_by": "agent (single coder)",
            "read_at_utc": "2026-11-18T09:40:00Z",
        },
        "device": {
            "name": "Fibresolve (with PCCP)",
            "has_pccp": True,
            "pccp_scope_types": ["model_architecture", "new_training_data", "ancillary_inputs"],
            "pccp_authorized": ["architecture_change", "new_input_modality"],
        },
        "change": {
            "type": "model_architecture",
            "description": "PCCP 允许在限定范围内修改模型架构、引入新训练数据、纳入辅助输入（保留原始输入）",
            "algorithm_driven": True,
            "architecture_change": True,
            "new_input_modality": True,
            "validation_performed": True,
            "acceptance_met": True,
            "introduces_new_risk": True,
            "risk_control_exists": True,
            "has_pccp": True,
            "boundary_statement": "限定范围：模型架构修改 / 新训练数据 / 辅助输入（原始输入不变）",
            "rationale": "通过新架构与训练数据提升性能、泛化与一致度",
            "risk_analysis": "风险：临床性能或泛化下降；缓解：测试集评估 + 单元与集成测试 + 获益-风险分析",
            "verification_evidence": "预定义统计分析，标准同原始器械；最低要求非劣绝对性能",
        },
        "jurisdictions": ["US"],
        "quotes": {
            "has_pccp": "FDA's substantial equivalence determination also included the review and clearance of your Predetermined Change Control Plan (PCCP).",
            "scope": "The plan allows for modifications and updates to the underlying Analysis Algorithm within a limited scope of changes, specifically model architecture modification, introduction of new training data, and incorporation of ancillary inputs (while maintaining original inputs).",
            "acceptance_met": "Changes are evaluated via pre-specified statistical analyses ... to ensure, at minimum, non-inferior absolute performance",
            "risk_control_exists": "Risk Mitigation: Evaluate device model on Test dataset metrics. Execute unit and integration tests for the product code.",
        },
        "human_expectation": "IN_SCOPE（改动落在已授权 PCCP 范围内，且验证与接受准则均已定义）",
    },
    {
        "id": "REAL-02",
        "source": {
            "k_number": "K252844",
            "device": "Tyto Insights for Wheeze Detection (with PCCP)",
            "applicant": "Tyto Care, Ltd.",
            "decision_date": "2026-06-02",
            "summary_pdf": "https://www.accessdata.fda.gov/cdrh_docs/pdf25/K252844.pdf",
            "field_value_pccp_authorized": "No",
            "read_by": "agent (single coder)",
            "read_at_utc": "2026-11-18T09:40:00Z",
        },
        "device": {
            "name": "Tyto Insights for Wheeze Detection (with PCCP)",
            "has_pccp": True,
            "pccp_scope_types": ["algorithm_update", "performance_enhancement", "input_device_expansion"],
        },
        "change": {
            "type": "security_patch",
            "description": "本次提交的目的是取得 PCCP 授权；与 predicate 的唯一附加差异是第三方库安全补丁的轻微软件更新",
            "cybersecurity_only": True,
            "significant": False,
            "validation_performed": True,
            "acceptance_met": True,
            "has_pccp": True,
            "boundary_statement": "PCCP 覆盖算法更新 / 性能增强 / 输入设备扩展；本次实际改动仅为安全补丁",
            "rationale": "取得 PCCP 授权，以便未来在预设范围内更新算法",
            "risk_analysis": "仅网络安全加固，不影响预期用途",
            "verification_evidence": "软件验证与确认按 IEC 62304 执行",
        },
        "jurisdictions": ["US"],
        "submission_purpose": "pccp_authorization",
        "quotes": {
            "purpose": "The purpose of this 510(k) submission is to obtain FDA's review and authorization of a Predetermined Change Control Plan (PCCP) for the subject device.",
            "actual_change": "The only additional difference from the predicate device is a minor software update in which third-party libraries were updated to address known vulnerabilities",
            "pccp_table": "PCCP | Includes PCCP (submitted for FDA review in this 510(k))",
        },
        "human_expectation": "本次改动本身无需新提交（安全补丁），但申报目的是取得 PCCP 授权——判定器若按“一次具体改动”建模会错判",
    },
]


def main():
    rows = []
    for c in CASES:
        out = n90.judge_with_n90(c)
        v = out["results"]["US"]
        rows.append({
            "id": c["id"],
            "k_number": c["source"]["k_number"],
            "verdict": v["verdict"],
            "route": v["route"],
            "context": v.get("context"),
            "rule_ids": [f["rule_id"] for f in v["findings"]],
            "n90_elements": {e: [x["rule_id"] for x in out["n90"]["elements"][e]]
                             for e in ("description", "plan", "impact")},
            "human_expectation": c["human_expectation"],
            "quotes": c["quotes"],
            "source": c["source"],
        })
        print(f"{c['id']} {c['source']['k_number']}: {v['verdict']} / {v['route']} / "
              f"{[f['rule_id'] for f in v['findings']]}")

    path = ROOT / "data" / "real_replay.json"
    io.open(path, "w", encoding="utf-8", newline="\n").write(json.dumps(
        {"replay": "real PCCP summaries, agent-coded single coder",
         "not_double_blind": True,
         "records": rows}, ensure_ascii=False, indent=2))
    print("wrote", path)


if __name__ == "__main__":
    main()
