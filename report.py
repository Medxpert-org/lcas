"""把 bench 结果渲染成单文件 HTML 成绩单。跑法：python report.py"""
from __future__ import annotations

import html
import json
from pathlib import Path

import evidence
from judge import judge

HERE = Path(__file__).parent
OUT = HERE / "bench-report.html"

DOMAIN_LABEL = {"device": "医疗器械", "drug": "药品", "auto": "汽车"}


def main():
    data = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
    cases = data["cases"]

    rows, checks, matches, fn, fp, pack_ok = [], 0, 0, [], [], 0
    per_domain = {}
    adv_total, adv_hit = 0, 0
    divergences = []

    for case in cases:
        out = judge(case)
        dom = DOMAIN_LABEL.get(case.get("domain", "device"), "医疗器械")
        for jur, res in out["results"].items():
            checks += 1
            exp = case["expected"].get(jur)
            hit = exp == res["verdict"]
            matches += 1 if hit else 0
            per_domain.setdefault(dom, [0, 0])
            per_domain[dom][0] += 1
            per_domain[dom][1] += 1 if hit else 0
            if exp in ("OUT_OF_SCOPE", "BLOCK") and res["route"] == "PASS":
                fn.append(f"{case['id']}/{jur}")
            if exp in ("NOT_REQUIRED", "IN_SCOPE") and res["route"] == "BLOCK":
                fp.append(f"{case['id']}/{jur}")
            if case["id"].startswith("ADV"):
                adv_total += 1
                adv_hit += 1 if res["route"] == "BLOCK" else 0
            if evidence.verify(evidence.build(case, res), case)[0]:
                pack_ok += 1
            rows.append((case["id"], jur, exp, res["verdict"], res["route"],
                         res["confidence"], hit,
                         "、".join(f["rule_id"] for f in res["findings"]) or "—",
                         dom))
        if out["divergence"]["divergent"] and len(out["results"]) > 1:
            divergences.append((case["id"], out["results"], out["divergence"]["note"]))

    acc = matches / checks if checks else 0
    cells = []
    for r in rows:
        cls = "ok" if r[6] else "no"
        cells.append(
            f'<tr><td class="m">{html.escape(r[0])}</td><td>{html.escape(r[8])}</td>'
            f'<td class="m">{html.escape(r[1])}</td>'
            f'<td class="m">{html.escape(str(r[2]))}</td><td class="m">{html.escape(r[3])}</td>'
            f'<td class="m">{html.escape(r[4])}</td><td class="m">{html.escape(r[5])}</td>'
            f'<td class="{cls}">{"一致" if r[6] else "不一致"}</td>'
            f'<td class="rule">{html.escape(r[7])}</td></tr>')

    dom_rows = "".join(
        f"<tr><td>{k}</td><td class='m'>{v[0]}</td><td class='m'>{v[1]}</td>"
        f"<td class='m'>{v[1]/v[0]*100:.0f}%</td></tr>" for k, v in per_domain.items())

    div_html = ""
    for cid, res, note in divergences:
        chips = " ".join(
            f"<span class='chip'><b>{j}</b>{r['verdict']}</span>" for j, r in res.items())
        div_html += f"<div class='divc'><div class='dh'>案例 {html.escape(cid)}</div><div class='chips'>{chips}</div><p>{html.escape(note)}</p></div>"

    tpl = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LCAS 判定器成绩单 v0.2</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><rect width='16' height='16' fill='%23101418'/><rect x='3' y='7' width='10' height='2' fill='%23F2F4F2'/></svg>">
<style>
:root{{--ink:#101418;--ink2:#3A4248;--ink3:#6E7880;--paper:#F2F4F2;--rule:#CFD5D2;--deep:#1F4A46;--alert:#A33A2E}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);
font-family:"PingFang SC","Microsoft YaHei","Noto Sans SC",system-ui,sans-serif;
-webkit-font-smoothing:antialiased}}
.m{{font-variant-numeric:tabular-nums;font-family:"JetBrains Mono",Consolas,monospace;font-size:12.5px}}
.wrap{{max-width:1180px;margin:0 auto;padding:44px 44px 64px}}
h1{{font-size:30px;line-height:1.25;margin:0 0 10px;letter-spacing:-.01em}}
.lead{{color:var(--ink2);font-size:14.5px;line-height:1.75;max-width:760px;margin:0 0 34px}}
.big{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--rule);
border:1px solid var(--rule);margin:0 0 34px}}
.big div{{background:var(--paper);padding:20px 18px}}
.big em{{display:block;font-size:11.5px;letter-spacing:.06em;color:var(--ink3);font-style:normal;margin-bottom:9px}}
.big b{{font-size:26px;font-variant-numeric:tabular-nums;display:block;line-height:1.1}}
.big span{{font-size:11.5px;color:var(--ink3)}}
h2{{font-size:13px;letter-spacing:.05em;color:var(--ink3);margin:38px 0 14px;font-weight:600}}
table{{width:100%;border-collapse:collapse;table-layout:fixed;font-size:12.5px}}
col.w1{{width:11%}} col.w2{{width:9%}} col.w3{{width:9%}} col.w4{{width:13%}}
col.w5{{width:13%}} col.w6{{width:8%}} col.w7{{width:8%}} col.w8{{width:7%}} col.w9{{width:22%}}
th{{text-align:left;font-weight:600;color:var(--ink3);font-size:11px;padding:8px 8px;
border-bottom:1px solid var(--ink);letter-spacing:.03em}}
td{{padding:7px 8px;border-bottom:1px solid var(--rule);vertical-align:top}}
td.rule{{color:var(--ink3);font-size:11px;word-break:break-all}}
td.ok{{color:var(--deep);font-weight:600}}
td.no{{color:var(--alert);font-weight:600}}
.chips{{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}}
.chip{{border:1px solid var(--rule);padding:5px 9px;font-size:11.5px;font-family:Consolas,monospace}}
.chip b{{color:var(--ink3);margin-right:7px;font-weight:600}}
.divc{{border-left:2px solid var(--deep);padding:4px 0 4px 14px;margin:0 0 16px}}
.dh{{font-size:12px;color:var(--ink3)}}
.divc p{{margin:6px 0 0;font-size:12.5px;color:var(--ink2);line-height:1.7}}
.foot{{margin-top:40px;padding-top:14px;border-top:1px solid var(--rule);color:var(--ink3);font-size:11.5px;line-height:1.8}}
@media (max-width:760px){{.wrap{{padding:26px 18px}}.big{{grid-template-columns:1fr 1fr}}}}
</style></head><body><div class="wrap">
<h1>变更判定器 成绩单 <span class="m">v0.2</span></h1>
<p class="lead">{len(cases)} 个案例、{checks} 次法域判定，覆盖医疗器械、药品、汽车三套制度。
唯一必须为零的指标是「该拦却放行」。成绩单由 <b>bench.py</b> 实跑生成，不是手写。</p>

<div class="big">
  <div><em>判定一致率</em><b>{matches}/{checks}</b><span>{acc*100:.0f}%</span></div>
  <div><em>安全方向漏判</em><b>{len(fn)}</b><span>该拦却放行</span></div>
  <div><em>离线复跑 MATCH</em><b>{pack_ok}/{checks}</b><span>证据包可独立重算</span></div>
  <div><em>对抗样本被拦</em><b>{adv_hit}/{adv_total}</b><span>文本无法说服规则</span></div>
</div>

<h2>分行业</h2>
<table><colgroup><col class="w1"><col class="w3"><col class="w3"><col class="w3"></colgroup>
<thead><tr><th>行业</th><th>判定数</th><th>一致</th><th>一致率</th></tr></thead>
<tbody>{dom_rows}</tbody></table>

<h2>跨法域并判</h2>
{div_html or "<p class='lead'>本次运行无差异案例。</p>"}

<h2>逐例明细</h2>
<table><colgroup><col class="w1"><col class="w2"><col class="w3"><col class="w4"><col class="w5"><col class="w6"><col class="w8"><col class="w8"><col class="w9"></colgroup>
<thead><tr><th>案例</th><th>行业</th><th>法域</th><th>期望</th><th>实际</th><th>路由</th><th>置信</th><th>判定</th><th>命中规则</th></tr></thead>
<tbody>{"".join(cells)}</tbody></table>

<div class="foot">
成绩单口径：预期结论按法规人工标注，不是监管认可；判定器输出为决策建议，非合规结论。<br>
跨法域差异不合并展示，差异归因区分「制度是否承认预定变更免责」与「规则覆盖缺口」两类。<br>
生成于 {len(cases)} 例数据集 · 规则 {len(__import__("judge").RULES)} + {sum(len(v) for v in __import__("domains").DOMAIN_RULES.values())} 条 · 纯标准库实现 · 可离线复跑
</div></div></body></html>"""
    OUT.write_text(tpl, encoding="utf-8")
    print(f"written {OUT}  chars={len(tpl)}  cases={len(cases)} checks={checks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
