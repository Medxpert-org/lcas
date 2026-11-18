#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fetch_openfda_510k.py —— 抓取并冻结一份**外部真实记录**的 510(k) 队列。

为什么要它：此前的语料是自制的，评审一句"自己造的语料证明不了什么"就废了。
本脚本只做一件可核验的事——从 openFDA 取记录、原样留存、算出哈希与抓取时间，
让"这份数据是外部来的、且没被改过"可被第三方独立复核。

冻结产物（两件，缺一不可）：
  data/openfda_510k_<cohort>.json   原始记录（不经任何加工）
  data/openfda_510k_<cohort>.manifest.json   sha256 + 抓取时间 + 查询语句 + 记录数 + 分页轨迹

用法：
  python tools/fetch_openfda_510k.py --query 'device_name:"software"' --limit 300
  python tools/fetch_openfda_510k.py --verify data/openfda_510k_software.json

边界：只记录**登记信息**（K 号、器械名、申请号、决议日期、产品码），
不推断"是否 AI""是否 PCCP"——判断留给人工与判定器，脚本不越界。
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

BASE = "https://api.fda.gov/device/510k.json"
ROOT = pathlib.Path(__file__).resolve().parents[1]


def fetch(query, limit, page_size=100):
    recs, skip = [], 0
    while len(recs) < limit:
        n = min(page_size, limit - len(recs))
        url = f"{BASE}?search={urllib.parse.quote(query)}&limit={n}&skip={skip}"
        req = urllib.request.Request(url, headers={"User-Agent": "lcas-corpus-fetch/0.1"})
        with urllib.request.urlopen(req, timeout=40) as r:
            body = json.loads(r.read().decode("utf-8"))
        batch = body.get("results", [])
        if not batch:
            break
        recs += batch
        skip += len(batch)
        if len(recs) >= body.get("meta", {}).get("results", {}).get("total", 0):
            break
        time.sleep(0.2)          # 不给上游压力，也避免被限流
    return recs


def freeze(query, limit, out_path):
    recs = fetch(query, limit)
    raw = json.dumps(recs, ensure_ascii=False, sort_keys=True, indent=2)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    data = {"query": query, "records": recs}
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    man = {
        "file": out_path.name,
        "sha256": digest,
        "record_count": len(recs),
        "query": query,
        "limit": limit,
        "fetched_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": BASE,
        "note": "记录未经加工；哈希为 records 数组的规范化 JSON（sort_keys + indent=2）",
    }
    (out_path.parent / (out_path.stem + ".manifest.json")).write_text(
        json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
    return man


def verify(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    man = json.loads((path.parent / (path.stem + ".manifest.json")).read_text(encoding="utf-8"))
    raw = json.dumps(data["records"], ensure_ascii=False, sort_keys=True, indent=2)
    got = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    ok = got == man["sha256"] and len(data["records"]) == man["record_count"]
    print(json.dumps({"file": path.name, "match": ok, "expected": man["sha256"],
                      "actual": got, "count": len(data["records"]),
                      "fetched_at_utc": man["fetched_at_utc"]}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--query")
    ap.add_argument("--limit", type=int, default=300)
    ap.add_argument("--name", default="software")
    ap.add_argument("--verify")
    a = ap.parse_args(argv)
    if a.verify:
        return verify(pathlib.Path(a.verify))
    if not a.query:
        ap.error("需要 --query 或 --verify")
    out = ROOT / "data" / f"openfda_510k_{a.name}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    man = freeze(a.query, a.limit, out)
    print(json.dumps(man, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
