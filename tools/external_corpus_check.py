# -*- coding: utf-8 -*-
"""外部语料检验：用 FDA openFDA 的真实 510(k) 记录当"别人的语料"。

为什么要这个：
    本项目 55 个案例全是自造。自造语料只能证明内部一致，不能证明面对真实监管
    数据时不崩。openFDA 的 Special 510(k) 是**真实发生过的器械变更申报**
    （FDA 已裁定"这次变更必须提交"），是目前唯一免费、可编程访问、带结论的真实语料。

做法：
    1. 抓 clearance_type=Special 且 device_name 含 software 的记录（真实变更正例）；
    2. 冻结成 JSON 并给出 sha256 语料指纹（别人可复现同一份语料）；
    3. 把这些记录喂给判定器。字段缺失的，按 fail-closed 应一律 UNCERTAIN；
    4. 报告"可判定率"——这个数字就是把人真实的短板量化出来。

跑法：
    python tools/external_corpus_check.py
    python tools/external_corpus_check.py --limit 100 --offline   # 用已冻结的语料
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / "data"
CORPUS = DATA / "external_corpus_510k_special_software.json"

BASE = "https://api.fda.gov/device/510k.json"
QUERY = 'clearance_type:"Special" AND device_name:software'


def fetch(limit: int) -> dict:
    url = BASE + "?search=" + urllib.parse.quote(QUERY) + "&limit=%d" % min(limit, 100)
    with urllib.request.urlopen(url, timeout=60) as r:
        raw = json.loads(r.read().decode("utf-8"))
    recs = []
    for d in raw.get("results", []):
        recs.append({
            "k_number": d.get("k_number"),
            "decision_date": d.get("decision_date"),
            "clearance_type": d.get("clearance_type"),
            "device_name": d.get("device_name"),
            "applicant": d.get("applicant"),
            "product_code": d.get("product_code"),
        })
    recs.sort(key=lambda x: (x["k_number"] or ""))
    return {
        "_note": "Real FDA 510(k) modification submissions. Consequence label: this change DID require a submission.",
        "_source": "https://open.fda.gov/apis/device/510k/",
        "_query": QUERY,
        "records": recs,
    }


def digest(obj: dict) -> str:
    blob = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def to_case(rec: dict) -> dict:
    """把一条真实记录变成判定器输入。字段只能从元数据得到，因此故意留空未知项。"""
    return {
        "id": rec["k_number"],
        "domain": "medical",
        "jurisdictions": ["US"],
        "device": {"name": rec["device_name"] or "", "has_pccp": False},
        "change": {
            "type": "unknown",
            "description": "真实 510(k) 记录，变更内容需从 510(k) Summary/SSED 原文抽取",
            # 元数据里没有这些字段 → 不猜，一律留空，交给 fail-closed
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()

    DATA.mkdir(exist_ok=True)
    if args.offline and CORPUS.exists():
        corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
        print("offline: 使用已冻结语料")
    else:
        corpus = fetch(args.limit)
        CORPUS.write_text(json.dumps(corpus, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("fetched: %d records -> %s" % (len(corpus["records"]), CORPUS))

    dg = digest(corpus)

    sys.path.insert(0, str(ROOT))
    from judge import judge  # noqa

    judged = {"OUT_OF_SCOPE": 0, "NOT_REQUIRED": 0, "IN_SCOPE": 0, "UNCERTAIN": 0}
    for rec in corpus["records"]:
        out = judge(to_case(rec))
        v = out["results"]["US"]["verdict"]
        judged[v] = judged.get(v, 0) + 1

    n = len(corpus["records"])
    decidable = n - judged["UNCERTAIN"]
    print()
    print("=== 外部语料检验（FDA openFDA / Special 510(k) / software）===")
    print("语料条数        %d" % n)
    print("语料指纹        %s" % dg)
    print("判定分布        %s" % json.dumps(judged, ensure_ascii=False))
    print("可判定率        %d/%d = %.1f%%" % (decidable, n, 100.0 * decidable / max(n, 1)))
    print()
    if decidable == 0:
        print("结论：字段全部缺失，判定器全部 fail-closed 进人工。")
        print("这不是判定器坏了，这正是缺口所在——")
        print("真实数据里**没有结构化字段**，只有 510(k) Summary 的叙述文字；")
        print("没有『叙述 → 字段』的抽取层，真实案例一条也判不了。")
    else:
        print("结论：%d 条可判定，需逐条核对抽取质量。" % decidable)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
