"""跨行业判定域库：同一台引擎，换一套法条锚。

医械在 judge.py（PCCP / 重大软件更新 / AI Act 43(4)）；
这里挂药品（ICH Q12 PACMP + EU Variations）与汽车（UN R156 SUMS + RXSWIN）。

行业差异只在"规则来源"，不在"计算结构"：
    输入 = 变更 + 已批准范围
    输出 = 在范围 / 超范围 / 无法判定（+ 依据条款 + 原文锚 + 可复核）
"""


def _ch(c):
    return c["change"]


def _dv(c):
    return c["device"]


DOMAIN_RULES = {
    # ------------------------------------------------------------ 药品
    "drug": [
        dict(id="DR-INTENDED-USE", jur="EU", domain="drug", effect="OUT_OF_SCOPE",
             article="Directive 2001/83/EC Art.19；Reg (EU) 2024/1701（Type II 变更）",
             desc="适应症/预期用途改变 → 属重大变更，须提交 Type II 变更或新上市许可申请，不得依 PACMP 实施",
             test=lambda c: bool(_ch(c).get("intended_use_changed"))),
        dict(id="DR-CN-INTENDED-USE", jur="CN", domain="drug", effect="OUT_OF_SCOPE",
             article="《药品注册管理办法》补充申请事项；NMPA 药品上市后变更管理办法",
             desc="适应症/预期用途改变 → 须提出补充申请，不属于 PACMP 可覆盖的范围",
             test=lambda c: bool(_ch(c).get("intended_use_changed"))),
        dict(id="DR-PACMP-IN", jur="EU", domain="drug", effect="IN_SCOPE",
             article="ICH Q12 §4 PACMP；EU Reg (EU) 2024/1701 既定条件（EC）",
             desc="变更落在已批准 PACMP 描述的条件与承诺范围内 → 可依 PACMP 实施",
             test=lambda c: bool(_dv(c).get("has_pacmp")) and bool(_ch(c).get("in_approved_scope"))),
        dict(id="DR-PACMP-OUT", jur="EU", domain="drug", effect="OUT_OF_SCOPE",
             article="ICH Q12 §4 PACMP（超出所述条件的处理）",
             desc="变更超出 PACMP 所述条件 → 需另行提交变更（variation）",
             test=lambda c: bool(_dv(c).get("has_pacmp")) and not bool(_ch(c).get("in_approved_scope"))),
        dict(id="DR-VAR-MAJOR", jur="EU", domain="drug", effect="OUT_OF_SCOPE",
             article="Commission Reg (EU) 2024/1701（2026-01-15 适用）",
             desc="影响安全性/有效性的重大变更 → 须提交 Type II 类变更",
             test=lambda c: bool(_ch(c).get("significant")) and not bool(_ch(c).get("in_approved_scope"))),
        dict(id="DR-PACMP-ABSENT", jur="EU", domain="drug", effect="OUT_OF_SCOPE",
             article="ICH Q12 §4（无 PACMP 时的默认路径）",
             desc="无已批准 PACMP 而拟变更 → 走常规变更程序",
             test=lambda c: not bool(_dv(c).get("has_pacmp")) and bool(_ch(c).get("significant"))),
        dict(id="DR-COND-MET", jur="EU", domain="drug", effect="BLOCK",
             article="ICH Q12 §4 PACMP（承诺与条件）",
             desc="在 PACMP 范围内但所述条件/承诺未满足 → 不可实施，先补条件",
             test=lambda c: bool(_dv(c).get("has_pacmp")) and bool(_ch(c).get("in_approved_scope"))
             and not bool(_ch(c).get("conditions_met"))),
        dict(id="DR-CN-PACMP", jur="CN", domain="drug", effect="IN_SCOPE",
             article="国家药监局 2025 年第 119 号公告（PACMP 国内可用；配套 2023 年第 108 号）",
             desc="已批准 PACMP 范围内的变更 → 按方案执行并在年报中报告",
             test=lambda c: bool(_dv(c).get("has_pacmp")) and bool(_ch(c).get("in_approved_scope"))
             and bool(_ch(c).get("conditions_met"))),
        dict(id="DR-CN-SUPPL", jur="CN", domain="drug", effect="OUT_OF_SCOPE",
             article="NMPA 药品上市后变更管理办法（补充申请）",
             desc="超出 PACMP 范围或影响质量/疗效 → 需补充申请",
             test=lambda c: (not bool(_dv(c).get("has_pacmp"))) or not bool(_ch(c).get("in_approved_scope"))),
    ],
    # ------------------------------------------------------------ 汽车
    "auto": [
        dict(id="AU-INTENDED-USE", jur="UN", domain="auto", effect="OUT_OF_SCOPE",
             article="UN R156 §7.1.1（批准范围）+ §7.2.1.2.1（须取得批准扩展）",
             desc="预期用途/功能范围改变且影响已批准系统合规性或涉安全关键功能 → 须取得型式批准扩展",
             test=lambda c: bool(_ch(c).get("intended_use_changed"))
             and (bool(_ch(c).get("affects_compliance")) or bool(_ch(c).get("safety_critical")))),
        dict(id="AU-INTENDED-USE-REVIEW", jur="UN", domain="auto", effect="UNCERTAIN",
             article="UN R156 §7.1.1（制造商评估义务）；§7.2.1.2.1 未直接覆盖该情形",
             desc="预期用途/功能范围改变，但制造商声称不影响合规性 → 属须人工裁量的边界，不得据此放行",
             test=lambda c: bool(_ch(c).get("intended_use_changed"))
             and not bool(_ch(c).get("affects_compliance")) and not bool(_ch(c).get("safety_critical"))),
        dict(id="AU-SUMS-OK", jur="UN", domain="auto", effect="NOT_REQUIRED",
             article="UN R156 §7.1.1（SUMS 过程）+ §7.2.1.2.1",
             desc="更新经制造商评估不影响已批准系统的合规性，且 RXSWIN 记录同步 → 无需型式批准变更",
             test=lambda c: bool(_ch(c).get("in_approved_scope")) and not bool(_ch(c).get("affects_compliance"))
             and bool(_ch(c).get("record_synced")) and not bool(_ch(c).get("intended_use_changed"))
             and not bool(_ch(c).get("safety_critical"))),
        dict(id="AU-SUMS-OUT", jur="UN", domain="auto", effect="OUT_OF_SCOPE",
             article="UN R156 §7.2.1.2.1（导致型式批准扩展/新批准须更新 RXSWIN）",
             desc="更新影响已批准系统的合规性 → 须报型式批准机构并变更批准",
             test=lambda c: bool(_ch(c).get("affects_compliance"))),
        dict(id="AU-RXSWIN", jur="UN", domain="auto", effect="BLOCK",
             article="UN R156 §7.1.2.3（可审计登记册）",
             desc="RXSWIN 未同步更新 → 软件状态无法追溯，更新不可实施",
             test=lambda c: not bool(_ch(c).get("record_synced"))),
        dict(id="AU-SAFETY", jur="UN", domain="auto", effect="OUT_OF_SCOPE",
             article="UN R156 §7.1.1 + UN R155（网络安全）",
             desc="涉安全关键功能（制动/转向/动力输出）→ 必须走批准变更",
             test=lambda c: bool(_ch(c).get("safety_critical"))),
    ],
}
