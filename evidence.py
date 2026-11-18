"""证据包：让裁决可被第三方离线重算。

设计要点：
- payload 规范化（键排序 + 紧凑分隔符）后哈希，任何人拿到同样输入与同样实现，
  都能重算出同一个 fingerprint → 一致即 MATCH。
- case_sha256 绑定原始案例，防止"换个案例套同一结论"。
"""
from __future__ import annotations

import hashlib
import json

SCHEMA = "lgd-evidence/0.1"


def canon(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build(case, result):
    payload = {
        "schema": SCHEMA,
        "case_id": case.get("id"),
        "jurisdiction": result["jurisdiction"],
        "verdict": result["verdict"],
        "route": result["route"],
        "confidence": result["confidence"],
        "rules": sorted(f["rule_id"] for f in result["findings"]),
        "rule_fingerprints": sorted(f["fingerprint"] for f in result["findings"]),
        "case_sha256": sha(canon(case)),
    }
    return {"payload": payload, "fingerprint": sha(canon(payload))}


def verify(pack, case) -> tuple[bool, str]:
    p = pack.get("payload") or {}
    if sha(canon(p)) != pack.get("fingerprint"):
        return False, "payload 被改动，指纹不符"
    if case is not None and p.get("case_sha256") != sha(canon(case)):
        return False, "案例与证据包不匹配"
    return True, "MATCH"
