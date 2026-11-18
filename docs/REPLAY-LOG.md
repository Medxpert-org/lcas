# 真实材料回放日志

2026-11-18 · 2 条真实 PCCP summary · 单编码人（agent）· **非双盲**

原始记录：`data/real_replay.json`；复跑：`python tools/replay_real_pccp.py`

## 为什么要做这个

所有"领先"的说法，最后都会被追问一句"你跑过真材料吗"。此前 55 个案例是自己写的，
评审一句"自己造的证明不了什么"就废。这里用**FDA 已授权的真实 PCCP summary**做回放。

方法约束：字段由人读 PDF 后手填，**每个字段必须有原文 quote**；没有 quote 的字段不填。

## 两条记录

### REAL-01 · K252041 · Fibresolve (with PCCP) · Imvaria

PCCP 明确授权三类改动：模型架构修改、引入新训练数据、纳入辅助输入（保留原始输入）。
接受准则：预定义统计分析，**最低要求非劣绝对性能**。风险与缓解写在同一张影响评估表里。

| 要素 | 判定器输出 |
|---|---|
| 裁决 | **IN_SCOPE / PASS** |
| 命中规则 | `US-PCCP-OK` |
| N90 要素 | 描述变更 / 变更计划 / 影响评估 均有落位 |

**与人工判读一致。**

### REAL-02 · K252844 · Tyto Insights for Wheeze Detection (with PCCP) · Tyto Care

summary 原文："The purpose of this 510(k) submission is to obtain FDA's review and authorization of a
Predetermined Change Control Plan (PCCP)"——**这次提交的目的就是拿到 PCCP 授权**；
与 predicate 的唯一附加差异是第三方库安全补丁。

| 要素 | 判定器输出 |
|---|---|
| 裁决 | **OUT_OF_SCOPE / BLOCK** |
| 命中规则 | `US-PCCP-R2`（类型不在清单）、`US-SW-Q1`（仅安全加固 → 无需提交） |

**与人工判读不一致。** 人工判断：安全补丁本身不需要新提交，但申报目的是取得 PCCP。

## 回放抓出的两个真问题

### 问题一（已修）：把"改架构"当越界，误拦真实授权

初版 `US-PCCP-R3` 的判据是"触达架构/输入模态/输出即越界"，不看 PCCP 到底授权了什么。
K252041 的 PCCP **明确授权架构修改与辅助输入**，却被判 `OUT_OF_SCOPE`——这是误拦。

修法：边界授权是**逐项**的。新增 `device.pccp_authorized` 白名单，只有"触达但未被逐项授权"才算越界
（`judge._unauthorized_boundaries`）。这同时保住合成案例 US-02：它只授权"重训"却改了输入模态，仍判越界。

回归：59/59 一致率、fuzz 0 违例、26+3 = 29 条测试全过。

### 问题二（未修，登记为缺陷）：把"申报目的"当成"一次改动"

判定器的输入模型假设 `change` 是一次具体改动。但 510(k) 的常见形态是——
**提交本身就是以 PCCP 授权为目的**，实际软件改动可能只是安全补丁（REAL-02 正是如此）。
按"一次改动"建模，就会把"PCCP 授权请求"读成"越界改动"。

修法需要新增输入字段（如 `submission_purpose: "pccp_authorization" | "specific_change"`），
并让 `US-PCCP-R1~R3` 在该字段为 `pccp_authorization` 时改走另一条分支。
**本次不改**：这动的是判定模型本身，必须有第二个人复核，不能我一边发现一边自己拍。

## 覆盖率现状（如实）

| 指标 | 值 |
|---|---|
| 真实记录回放 | **2**（目标 100） |
| 与人工一致 | 1 / 2 |
| 发现并修复的规则缺陷 | 1 |
| 登记未修的模型缺陷 | 1 |
| 编码人 | 1（非双盲） |

2 条不足以支撑任何统计结论，但足以证明一件事：**真实材料会把合成案例里看不出来的错逼出来**——
这一条已经发生，且已修复并加测试守住。

## 下一步（需人）

按 `docs/PCCP-FIELD-AUDIT.md` 的通道结论：`web_fetch` 可读 summary PDF，无法脚本化批量。
单条约 3–5 分钟人工判读；100 条约 6–8 小时。同时需要第二个编码人做双盲。
