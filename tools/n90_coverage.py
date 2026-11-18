#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""n90_coverage.py —— 生成 N90 覆盖矩阵（可复跑，不许手写）。

输出 docs/N90-COVERAGE.md：把 40 条规则按「要素 × 原则 × 法域」摊开，空位一律显式留白而不是省略。
`tests/test_n90_coverage.py` 会重算并与仓库里的文件逐字比对——**改了映射忘了重生成，CI 会红**。

用法：
  python tools/n90_coverage.py            # 写入 docs/N90-COVERAGE.md
  python tools/n90_coverage.py --check    # 只比对，不一致则 exit 1
"""
from __future__ import annotations

import io
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import judge        # noqa: E402
import domains      # noqa: E402
import n90          # noqa: E402

OUT = ROOT / "docs" / "N90-COVERAGE.md"


def _rules():
    """(rule_id, jurisdiction, domain) 全量清单。"""
    rows = [(r["id"], r["jur"], "device") for r in judge.RULES]
    for d, rs in domains.DOMAIN_RULES.items():
        rows += [(r["id"], r["jur"], d) for r in rs]
    return rows


def build():
    rules = _rules()
    lines = [
        "# N90 覆盖矩阵（自动生成，勿手改）",
        "",
        "由 `tools/n90_coverage.py` 从 `judge.py` / `domains.py` / `n90.py` 的映射实时计算。",
        "改规则或改映射后必须重跑；`tests/test_n90_coverage.py` 会比对，过期即 CI 失败。",
        "",
        "IMDRF N90 FINAL:2026 的三要素与五原则，本表只呈现**本仓规则落在哪一格**；",
        "格子空着就是空着，不补话，也不代表该原则不适用。",
        "",
        "## 一、要素 × 原则（规则条数）",
        "",
    ]
    header = "| 要素 | " + " | ".join(n90.PRINCIPLE_ZH[p] for p in n90.PRINCIPLES) + " | 小计 |"
    sep = "|---" * (len(n90.PRINCIPLES) + 2) + "|"
    lines += [header, sep]
    for e in n90.ELEMENTS:
        cells = []
        for p in n90.PRINCIPLES:
            ids = [rid for rid, (el, ps) in n90.MAPPING.items() if el == e and p in ps]
            cells.append(str(len(ids)) if ids else "—")
        total = len([1 for rid, (el, _) in n90.MAPPING.items() if el == e])
        lines.append(f"| {n90.ELEMENT_ZH[e]} | " + " | ".join(cells) + f" | {total} |")

    lines += ["", "## 二、逐条落位", "",
              "| 规则 | 法域 | 行业 | 要素 | 原则 |", "|---|---|---|---|---|"]
    for rid, jur, dom in rules:
        el, ps = n90.MAPPING.get(rid, (None, []))
        el_zh = n90.ELEMENT_ZH[el] if el else "**未映射**"
        p_zh = "、".join(n90.PRINCIPLE_ZH[p] for p in ps) or "—"
        lines.append(f"| `{rid}` | {jur} | {dom} | {el_zh} | {p_zh} |")

    unmapped = [rid for rid, _, _ in rules if rid not in n90.MAPPING]
    lines += ["", "## 三、法域分布", "", "| 法域 | 规则 | 叙述 |", "|---|---|---|"]
    for jur in ("US", "CN", "EU", "DR", "AU"):
        ids = [rid for rid, j, _ in rules if j == jur]
        if ids:
            lines.append(f"| {jur} | {len(ids)} | 见上表逐条落位 |")

    lines += ["", "## 四、缺口与结论（按数据写，不按期望写）", ""]
    lines.append(f"- 规则总数 **{len(rules)}**，已映射 **{len(rules) - len(unmapped)}**，"
                 f"未映射 **{len(unmapped)}**" + (f"（{', '.join(unmapped)}）" if unmapped else ""))
    for p in n90.PRINCIPLES:
        n = len([1 for _, ps in n90.MAPPING.values() if p in ps])
        lines.append(f"- 原则「{n90.PRINCIPLE_ZH[p]}」落点 {n} 条" + ("（**仅 1 条，薄弱**）" if n == 1 else ""))
    lines.append("")
    lines.append("注意：本表证明的是**规则可归位**，不是**判定符合 N90**（见 SPEC §9.3 主张边界）。")
    return "\n".join(lines) + "\n"


def main(argv):
    text = build()
    if "--check" in argv:
        cur = io.open(OUT, encoding="utf-8").read() if OUT.exists() else ""
        if cur != text:
            print("N90-COVERAGE.md 已过期：映射或规则变了，请重跑 tools/n90_coverage.py")
            return 1
        print("N90-COVERAGE.md 与映射一致")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(text)
    print(f"wrote {OUT} ({len(text.encode('utf-8'))} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
