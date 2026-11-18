"""不变量测试：穷举字段组合，验证判定器永不失守。

这是本项目的"可被外部检查"承诺的硬核部分：不是挑几个案例演示，而是把所有
布尔组合（含字段自相矛盾的组合）全跑一遍，断言六条不变量。

跑法：python fuzz.py
"""
from __future__ import annotations

import itertools
import time

from judge import judge, judge_one

# 医疗器械之外的两个行业域：同样要过不变量，不能只有医械被穷举
DOMAIN_FLAGS = {
    "drug": ["intended_use_changed", "in_approved_scope", "conditions_met", "significant"],
    "auto": ["intended_use_changed", "in_approved_scope", "affects_compliance",
             "record_synced", "safety_critical"],
}
DOMAIN_DEVFLAG = {"drug": "has_pacmp", "auto": "has_sums"}
DOMAIN_JURS = {"drug": ["EU", "CN"], "auto": ["UN"]}

FLAGS = [
    "new_intended_use", "architecture_change", "new_input_modality", "new_output",
    "algorithm_driven", "data_driven", "online_learning", "cybersecurity_only",
    "return_to_spec", "significant", "perf_significant_diff", "new_intended_use_dup",
]
FLAGS = FLAGS[:-1]  # 去掉占位

JURS = ["US", "CN", "EU"]


def build(flags: dict, has_pccp: bool, in_scope: bool, desc: str):
    ch = {"type": "model_retrain" if in_scope else "ui_text", "description": desc}
    ch.update(flags)
    return {
        "id": "fuzz",
        "jurisdictions": JURS,
        "device": {"name": "fuzz", "has_pccp": has_pccp,
                   "pccp_scope_types": ["model_retrain"] if has_pccp else []},
        "change": ch,
    }


def main():
    t0 = time.perf_counter()
    combos = 0
    judgments = 0
    viol = []
    nondet = 0

    for bits in itertools.product([False, True], repeat=len(FLAGS)):
        flags = dict(zip(FLAGS, bits))
        for has_pccp in (False, True):
            for in_scope in (False, True):
                for desc in ("字段自洽的变更描述", ""):
                    case = build(flags, has_pccp, in_scope, desc)
                    combos += 1
                    out = judge(case)
                    again = judge(case)
                    if out != again:
                        nondet += 1

                    for jur, res in out["results"].items():
                        judgments += 1
                        route = res["route"]
                        v = res["verdict"]

                        # INV-1 预期用途改变，任何法域都不得放行
                        if flags["new_intended_use"] and route == "PASS":
                            viol.append(("INV-1", jur, flags, v))
                        # INV-2 自学习，中国侧不得放行
                        if jur == "CN" and flags["online_learning"] and route == "PASS":
                            viol.append(("INV-2", jur, flags, v))
                        # INV-3 有 PCCP 时越过架构边界，美国侧不得放行
                        if jur == "US" and has_pccp and flags["architecture_change"] and route == "PASS":
                            viol.append(("INV-3", jur, flags, v))
                        # INV-4 规则全不命中时必须 UNCERTAIN（fail-closed）
                        if not res["findings"] and v != "UNCERTAIN":
                            viol.append(("INV-4", jur, flags, v))
                        # INV-5 未决必须走人工，不得静默通过
                        if v == "UNCERTAIN" and route != "REVIEW":
                            viol.append(("INV-5", jur, flags, v))
                        # INV-6 每条命中规则必须带非空指纹与法条锚
                        for f in res["findings"]:
                            if not f.get("fingerprint") or not f.get("article"):
                                viol.append(("INV-6", jur, flags, v))

    # ---------- 药品 / 汽车两域的不变量穷举 ----------
    for dom, keys in DOMAIN_FLAGS.items():
        for bits in itertools.product([False, True], repeat=len(keys)):
            flags = dict(zip(keys, bits))
            for dev in (False, True):
                case = {"id": "fuzz-" + dom, "domain": dom,
                        "device": {"name": "fuzz", DOMAIN_DEVFLAG[dom]: dev},
                        "change": dict(flags, type="fuzz", description="字段自洽的变更描述")}
                combos += 1
                for jur in DOMAIN_JURS[dom]:
                    out = judge_one(case, jur)
                    again = judge_one(case, jur)
                    if out != again:
                        nondet += 1
                    judgments += 1
                    route = out["route"]
                    v = out["verdict"]
                    # INV-1：预期用途改变，任何行业任何法域都不得放行
                    if flags.get("intended_use_changed") and route == "PASS":
                        viol.append(("INV-1", dom + "/" + jur, flags, v))
                    if not out["findings"] and v != "UNCERTAIN":
                        viol.append(("INV-4", dom + "/" + jur, flags, v))
                    if v == "UNCERTAIN" and route != "REVIEW":
                        viol.append(("INV-5", dom + "/" + jur, flags, v))
                    for f in out["findings"]:
                        if not f.get("fingerprint") or not f.get("article"):
                            viol.append(("INV-6", dom + "/" + jur, flags, v))

    dt = time.perf_counter() - t0
    print("=== 不变量测试 ===")
    print(f"字段组合        {combos}")
    print(f"法域判定        {judgments}")
    print(f"耗时            {dt*1000:.0f} ms（{judgments/dt:,.0f} 判定/秒）")
    print(f"确定性（重跑一致） {'100%' if nondet == 0 else f'{nondet} 次不一致'}")
    print(f"不变量违例      {len(viol)}")
    if viol:
        for v in viol[:10]:
            print("  ", v)
    else:
        print("  INV-1 预期用途改变永不放行 / INV-2 自学习中国侧永不放行 /")
        print("  INV-3 越架构边界美国侧永不放行 / INV-4 无命中必须未决 /")
        print("  INV-5 未决必走人工 / INV-6 每条裁决可追溯——全部通过")
    return 0 if not viol and nondet == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
