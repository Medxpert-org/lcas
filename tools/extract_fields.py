# -*- coding: utf-8 -*-
"""叙述 → 字段的抽取层（确定性、可审计、无模型调用）。

为什么不用大模型：
    抽取必须可复核。每条字段要么带一句原文引语，要么留空进人工；
    不允许"看起来像"就填。所以这里只用正则 + 否定窗口，且**宁缺勿猜**。

输出契约：
    extract(text) -> {
        "fields":   {字段名: True/False},        # 仅包含有证据的字段
        "evidence": [{field, value, quote, pattern}],
        "abstained": [字段名...],               # 文本里没有依据的字段
    }

字段名与 judge.py 的 change 字段一致，可直接喂给判定器。
"""
from __future__ import annotations

import re

# (字段, True/False, 正则, 规则 id)
PATTERNS = [
    # ---- 预期用途：FDA Special 510(k) 备忘录的标准句 ----
    ("new_intended_use", False,
     r"indication[s]?[\s/]*intended\s+use[^.]{0,120}?(has\s+not\s+changed|not\s+changed|remain[s]?\s+the\s+same|are\s+the\s+same|unaffected)",
     "IU-NEG-MEMO"),
    ("new_intended_use", False,
     r"(same\s+intended\s+use\s+and\s+(same\s+)?indications\s+for\s+use|do(es)?\s+not\s+create\s+a\s+new\s+intended\s+use|no\s+change\s+in\s+(the\s+)?intended\s+use)",
     "IU-NEG-SAME"),
    ("new_intended_use", True,
     r"(new\s+indication|expand(s|ed)?\s+(the\s+)?indications|intended\s+use\s+(has\s+)?(been\s+)?(changed|expanded)|new\s+intended\s+use)",
     "IU-POS"),

    # ---- 基本科学技术是否改变（对应架构/技术变更）----
    ("architecture_change", False,
     r"fundamental\s+scientific\s+technology[^.]{0,80}?(has\s+not\s+changed|same|unchanged)",
     "TECH-NEG"),
    ("architecture_change", True,
     r"(new\s+(deep\s+learning|machine\s+learning)\s+model|retrain(ed|ing)?|architecture\s+(change|modif|redesign)|new\s+algorithm\s+architecture)",
     "TECH-POS"),

    # ---- 新增输出 / 新功能模块（对应 new_output）----
    ("new_output", True,
     r"(add(s|ed)?\s+(a\s+)?(new\s+)?(software\s+)?(feature|module|parameter|measurement|license)|introduc(tion|es?)\s+of\s+(a\s+)?new|incorporat(es?|ed|ion))",
     "OUT-POS"),

    # ---- 算法驱动型更新 ----
    ("algorithm_driven", True,
     r"(algorithm\s+(change|update|modification)|signal\s+filtering|automatic(ally)?\s+analyz|automated\s+(analysis|calculation))",
     "ALGO-POS"),

    # ---- 是否引入新风险 ----
    ("introduces_new_risk", False,
     r"(no\s+new\s+questions\s+of\s+safety|did\s+not\s+identify\s+any\s+new|does\s+not\s+raise\s+additional\s+safety|no\s+impact\s+on\s+the\s+control\s+mechanisms)",
     "RISK-NEG"),
    ("introduces_new_risk", True,
     r"(new\s+hazard|introduces?\s+a\s+new\s+risk|new\s+risk\s+of)",
     "RISK-POS"),

    # ---- 验证与接受准则 ----
    ("validation_performed", True,
     r"(verification\s+and\s+validation\s+(activities\s+)?(were\s+)?performed|design\s+verification\s+activities\s+were\s+performed|performance\s+tests\s+have\s+been\s+completed)",
     "VAL-POS"),
    ("acceptance_met", True,
     r"(acceptance\s+criteria\s+(were|was)\s+met|met\s+their\s+respective\s+acceptance\s+criteria|predetermined\s+acceptance\s+criteria\s+were\s+met)",
     "ACC-POS"),

    # ---- 仅网络安全加固 ----
    ("cybersecurity_only", True,
     r"(cyber\s?security\s+(only|hardening)|solely\s+to\s+(improve|address)\s+cyber)",
     "CYBER-POS"),
]

NEG_WINDOW = 60  # 真值前 60 字符内出现否定词，则真值不成立


def _negated(text: str, start: int) -> bool:
    pre = text[max(0, start - NEG_WINDOW):start].lower()
    return bool(re.search(r"(\bnot\b|\bno\b|without|cannot|never)", pre))


def extract(text: str) -> dict:
    text = re.sub(r"\s+", " ", text)
    fields, evidence = {}, []
    for field, value, pat, pid in PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            if value is True and _negated(text, m.start()):
                continue
            quote = text[max(0, m.start() - 40):min(len(text), m.end() + 40)].strip()
            if field not in fields:
                fields[field] = value
                evidence.append({"field": field, "value": value,
                                 "quote": quote, "pattern": pid})
            break

    all_fields = {p[0] for p in PATTERNS}
    abstained = sorted(all_fields - set(fields))
    return {"fields": fields, "evidence": evidence, "abstained": abstained}


if __name__ == "__main__":
    import json, sys
    txt = open(sys.argv[1], encoding="utf-8").read() if len(sys.argv) > 1 else sys.stdin.read()
    print(json.dumps(extract(txt), ensure_ascii=False, indent=2))
