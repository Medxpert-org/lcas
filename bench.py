"""LGD-ChgBench v0.1 · 回归与证据包生成

跑法：python bench.py
输出：逐例对账表 + 三项硬指标（一致率 / 安全方向漏判 / 离线复跑）
"""
from __future__ import annotations

import json
from pathlib import Path

import evidence
from judge import judge
from judge import judge_one  # noqa: F401  (保持一致入口)

HERE = Path(__file__).parent
PACK_DIR = HERE / "packs"


def main():
    data = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
    cases = data["cases"]
    PACK_DIR.mkdir(exist_ok=True)

    rows = []
    checks = 0
    matches = 0
    false_neg = []      # 期望"要提交/拦截"，实际却放了 → 安全方向错误，必须为 0
    false_pos = []      # 期望"不需提交"，实际拦了 → 体验方向错误，可接受但要报
    pack_ok = 0
    pack_total = 0

    for case in cases:
        out = judge(case)
        for jur, res in out["results"].items():
            checks += 1
            exp = case["expected"].get(jur)
            got = res["verdict"]
            hit = exp == got
            matches += 1 if hit else 0
            if exp in ("OUT_OF_SCOPE", "BLOCK") and res["route"] == "PASS":
                false_neg.append(f"{case['id']}/{jur}")
            if exp in ("NOT_REQUIRED", "IN_SCOPE") and res["route"] == "BLOCK":
                false_pos.append(f"{case['id']}/{jur}")

            pack = evidence.build(case, res)
            (PACK_DIR / f"{case['id']}_{jur}.json").write_text(
                json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
            ok, why = evidence.verify(pack, case)
            pack_total += 1
            pack_ok += 1 if ok else 0

            rows.append((case["id"], jur, exp or "-", got, res["route"],
                         res["confidence"], "OK" if hit else "MISMATCH",
                         ",".join(f["rule_id"] for f in res["findings"]) or "-"))

    print("\n=== 逐例对账 ===")
    print(f"{'案例':<8}{'法域':<5}{'期望':<15}{'实际':<15}{'路由':<12}{'置信':<8}{'判定':<10}规则")
    for r in rows:
        print(f"{r[0]:<8}{r[1]:<5}{r[2]:<15}{r[3]:<15}{r[4]:<12}{r[5]:<8}{r[6]:<10}{r[7]}")

    print("\n=== 三项硬指标 ===")
    acc = matches / checks if checks else 0
    print(f"一致率            {matches}/{checks} = {acc*100:.1f}%")
    print(f"安全方向漏判      {len(false_neg)}  {('← ' + ', '.join(false_neg)) if false_neg else '（必须为 0，已达标）'}")
    print(f"误拦（可接受）    {len(false_pos)}  {('← ' + ', '.join(false_pos)) if false_pos else '（无）'}")
    print(f"离线复跑 MATCH    {pack_ok}/{pack_total} = {pack_ok/pack_total*100:.0f}%")

    # 跨法域差异样本
    print("\n=== 跨法域并判样本 ===")
    for case in cases:
        out = judge(case)
        if len(out["results"]) > 1:
            vs = " | ".join(f"{j}:{r['verdict']}" for j, r in out["results"].items())
            print(f"{case['id']:<8}{vs}")
            if out["divergence"]["divergent"]:
                print(f"         差异成立：{out['divergence']['note']}")

    return 0 if acc == 1.0 and not false_neg and pack_ok == pack_total else 1


if __name__ == "__main__":
    raise SystemExit(main())
