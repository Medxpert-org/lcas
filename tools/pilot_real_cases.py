# -*- coding: utf-8 -*-
"""真实案例试点：4 份 FDA 501(k) 原文摘录 → 抽取字段 → 判定器 → 对照真实后果。

标签的含义（必须写清楚，否则就是自欺）：
    这 4 条都是**FDA 实际收到并审过的变更申报**（Special / Traditional 510(k)），
    所以"真实后果"= 该变更被当成需要提交的变更处理（consequence label: SUBMITTED）。
    它是**后果标签**，不是规范标签——不能反过来证明"这个变更在规范上一定超范围"。

因此本脚本报告三件不同的事：
    1. 字段覆盖率：真实文书里能抽出多少字段（抽取层的能力）
    2. 判定结果：引擎在这些字段下给什么（判定层的能力）
    3. 一致性：引擎结论与后果标签是否对得上（有用性）

跑法：python tools/pilot_real_cases.py
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from extract_fields import extract          # noqa: E402
from judge import judge                      # noqa: E402

TOTAL_FIELDS = 11


def main() -> int:
    data = json.loads((ROOT / "data" / "pilot_texts.json").read_text(encoding="utf-8"))

    rows = []
    for rec in data:
        ex = extract(rec["excerpt"])
        case = {
            "id": rec["k_number"],
            "domain": "medical",
            "jurisdictions": ["US"],
            "device": {"name": rec["k_number"], "has_pccp": False},
            "change": dict(ex["fields"], type="real_510k_record",
                           description="抽取自 " + rec["url"]),
        }
        out = judge(case)
        res = out["results"]["US"]
        rows.append({
            "k": rec["k_number"],
            "type": rec["clearance_type"],
            "fields": len(ex["fields"]),
            "abstained": len(ex["abstained"]),
            "verdict": res["verdict"],
            "route": res["route"],
            "rules": [f.get("id") for f in res.get("findings", [])],
            "evidence": ex["evidence"],
        })

    print("=== 真实案例试点（%d 份 FDA 510(k) 原文摘录）===\n" % len(rows))
    for r in rows:
        print("%s (%s)  字段 %d/%d  abstain %d  → %-13s %-6s  %s" % (
            r["k"], r["type"], r["fields"], TOTAL_FIELDS, r["abstained"],
            r["verdict"], r["route"], ",".join(x for x in r["rules"] if x)))
        for e in r["evidence"][:3]:
            print("      [%s] %s ← \"%s…\"" % (e["pattern"], e["field"], e["quote"][:78]))
        print()

    n = len(rows)
    cov = sum(r["fields"] for r in rows) / (n * TOTAL_FIELDS)
    decided = sum(1 for r in rows if r["verdict"] != "UNCERTAIN")
    agree = sum(1 for r in rows if r["verdict"] == "OUT_OF_SCOPE")

    print("=== 汇总 ===")
    print("字段覆盖率        %.1f%%（平均每份文件抽出 %.1f/%d 个字段）" % (
        cov * 100, sum(r["fields"] for r in rows) / n, TOTAL_FIELDS))
    print("可判定率          %d/%d" % (decided, n))
    print("与后果标签一致    %d/%d（后果标签 = 该变更确实被作为需提交的变更处理）" % (agree, n))
    print()
    print("结论怎么读：")
    if decided < n:
        print("  文本里**有**证据（覆盖率不低），但规则层没有把'已提交的变更'映射成 OUT_OF_SCOPE。")
        print("  缺口从'抽不出字段'转到了'字段→规则映射'。这是进展，也是新的短板。")
    else:
        print("  字段与规则都对上了，可以进入下一关（扩大样本 + 抽第二人复核）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
