"""LCAS conformance kit — 任何人都能用它检验自己的变更判定实现。

用法：
    python conformance.py --impl ./your_judge.py            # 检验你的实现
    python conformance.py --impl ./judge.py --check-evidence # 同时校验证据字段
    python conformance.py --list                             # 列出数据集规模

被检验模块只需暴露二选一：
    adjudicate(case) -> {jurisdiction: verdict}            # 推荐
    judge(case)      -> {"results": {jur: {"verdict": ...}}}
verdict 取值必须属于：IN_SCOPE / NOT_REQUIRED / OUT_OF_SCOPE / UNCERTAIN / BLOCK

判定等级：
    L1 = 四值裁决全部正确（verdict conformance）
    L2 = L1 + 每条裁决带 article 与 fingerprint
    L3 = L2 + 离线证据包可重算（需实现方另行提供）
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
VALID = {"IN_SCOPE", "NOT_REQUIRED", "OUT_OF_SCOPE", "UNCERTAIN", "BLOCK"}


def load_impl(path: Path):
    spec = importlib.util.spec_from_file_location("impl_under_test", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"无法加载实现：{path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["impl_under_test"] = mod
    # 让实现自身目录里的同包模块（如 domains.py）可被导入
    parent = str(path.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    spec.loader.exec_module(mod)
    return mod


def run_impl(mod, case):
    if hasattr(mod, "adjudicate"):
        return dict(mod.adjudicate(case))
    if hasattr(mod, "judge"):
        out = mod.judge(case)
        return {j: r["verdict"] for j, r in out["results"].items()}, out
    raise SystemExit("实现必须提供 adjudicate(case) 或 judge(case)")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="lcas-conformance")
    ap.add_argument("--impl", type=str, help="待检验实现模块路径")
    ap.add_argument("--cases", type=str, default=str(HERE.parent / "cases.json"))
    ap.add_argument("--check-evidence", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)

    data = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    cases = data["cases"]

    if args.list:
        print(f"cases={len(cases)}  schema={data.get('schema')}")
        for c in cases[:3]:
            print(" ", c["id"], c["expected"])
        return 0

    if not args.impl:
        ap.print_help()
        return 2

    mod = load_impl(Path(args.impl))

    total = ok = 0
    bad, missing_ev = [], []
    for case in cases:
        got_any = run_impl(mod, case)
        got = got_any[0] if isinstance(got_any, tuple) else got_any
        full = got_any[1] if isinstance(got_any, tuple) else None
        for jur, exp in case["expected"].items():
            total += 1
            got_v = got.get(jur)
            if got_v == exp:
                ok += 1
            else:
                bad.append((case["id"], jur, exp, got_v))
            if args.check_evidence:
                if full is None:
                    missing_ev.append((case["id"], jur, "无 findings 输出"))
                else:
                    for f in full["results"][jur].get("findings", []):
                        if not f.get("article") or not f.get("fingerprint"):
                            missing_ev.append((case["id"], jur, f.get("rule_id")))

    print("=== LCAS 符合性检验 ===")
    print(f"实现        {args.impl}")
    print(f"判定一致    {ok}/{total} = {ok/total*100:.1f}%")
    if bad:
        print("不一致明细：")
        for b in bad[:12]:
            print(f"  {b[0]}/{b[1]}  期望 {b[2]}  实际 {b[3]}")
    if args.check_evidence:
        print(f"证据字段    {'全部合规' if not missing_ev else str(len(missing_ev)) + ' 处缺失'}")
        for m in missing_ev[:6]:
            print("  ", m)

    level = "L1" if ok == total else "未达标（L1 未通过）"
    if ok == total and args.check_evidence and not missing_ev:
        level = "L2"
    print(f"等级        {level}（L3 需离线证据包重算，另行校验）")
    return 0 if ok == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
