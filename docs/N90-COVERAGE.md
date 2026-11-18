# N90 覆盖矩阵（自动生成，勿手改）

由 `tools/n90_coverage.py` 从 `judge.py` / `domains.py` / `n90.py` 的映射实时计算。
改规则或改映射后必须重跑；`tests/test_n90_coverage.py` 会比对，过期即 CI 失败。

IMDRF N90 FINAL:2026 的三要素与五原则，本表只呈现**本仓规则落在哪一格**；
格子空着就是空着，不补话，也不代表该原则不适用。

## 一、要素 × 原则（规则条数）

| 要素 | 聚焦且有边界 | 基于风险 | 基于证据 | 透明 | 全生命周期视角 | 小计 |
|---|---|---|---|---|---|---|
| 描述变更（Description of Changes） | 19 | 4 | 1 | 1 | — | 20 |
| 变更计划（Change Plan） | — | — | 4 | 5 | — | 6 |
| 影响评估（Impact Assessment） | 1 | 9 | 4 | 4 | 5 | 14 |

## 二、逐条落位

| 规则 | 法域 | 行业 | 要素 | 原则 |
|---|---|---|---|---|
| `US-807-81-A3` | US | device | 描述变更（Description of Changes） | 聚焦且有边界 |
| `US-PCCP-R1` | US | device | 描述变更（Description of Changes） | 聚焦且有边界、透明 |
| `US-PCCP-R2` | US | device | 描述变更（Description of Changes） | 聚焦且有边界 |
| `US-PCCP-R3` | US | device | 描述变更（Description of Changes） | 聚焦且有边界 |
| `US-PCCP-R4` | US | device | 变更计划（Change Plan） | 基于证据、透明 |
| `US-SW-Q1` | US | device | 影响评估（Impact Assessment） | 基于风险 |
| `US-SW-Q2` | US | device | 影响评估（Impact Assessment） | 基于风险 |
| `US-SW-Q3` | US | device | 影响评估（Impact Assessment） | 基于风险 |
| `US-PCCP-OK` | US | device | 变更计划（Change Plan） | 基于证据、透明 |
| `CN-AI-LOCK` | CN | device | 描述变更（Description of Changes） | 聚焦且有边界 |
| `CN-ALG-DRIVEN` | CN | device | 描述变更（Description of Changes） | 聚焦且有边界、基于风险 |
| `CN-DATA-DRIVEN-DIFF` | CN | device | 影响评估（Impact Assessment） | 基于风险、基于证据 |
| `CN-DATA-DRIVEN-OK` | CN | device | 影响评估（Impact Assessment） | 基于证据 |
| `CN-NO-PCCP` | CN | device | 影响评估（Impact Assessment） | 聚焦且有边界、透明 |
| `CN-PERF-SIMPLIFY` | CN | device | 描述变更（Description of Changes） | 基于证据 |
| `CN-INTENDED-USE` | CN | device | 描述变更（Description of Changes） | 聚焦且有边界 |
| `CN-ARCH-CHANGE` | CN | device | 描述变更（Description of Changes） | 聚焦且有边界 |
| `CN-MINOR` | CN | device | 影响评估（Impact Assessment） | 全生命周期视角、基于风险 |
| `EU-43-4-PREDET` | EU | device | 影响评估（Impact Assessment） | 透明、全生命周期视角 |
| `EU-43-4-SUBSTANTIAL` | EU | device | 描述变更（Description of Changes） | 聚焦且有边界 |
| `EU-MDR-NB` | EU | device | 影响评估（Impact Assessment） | 基于风险、基于证据 |
| `EU-CYBER-MINOR` | EU | device | 影响评估（Impact Assessment） | 全生命周期视角、基于风险 |
| `EU-PERF-TUNE` | EU | device | 影响评估（Impact Assessment） | 基于证据、全生命周期视角 |
| `EU-CLASS-CHANGE` | EU | device | 描述变更（Description of Changes） | 聚焦且有边界、基于风险 |
| `EU-INTENDED-USE` | EU | device | 描述变更（Description of Changes） | 聚焦且有边界 |
| `DR-INTENDED-USE` | EU | drug | 描述变更（Description of Changes） | 聚焦且有边界 |
| `DR-CN-INTENDED-USE` | CN | drug | 描述变更（Description of Changes） | 聚焦且有边界 |
| `DR-PACMP-IN` | EU | drug | 变更计划（Change Plan） | 透明、基于证据 |
| `DR-PACMP-OUT` | EU | drug | 描述变更（Description of Changes） | 聚焦且有边界 |
| `DR-VAR-MAJOR` | EU | drug | 影响评估（Impact Assessment） | 基于风险 |
| `DR-PACMP-ABSENT` | EU | drug | 描述变更（Description of Changes） | 聚焦且有边界 |
| `DR-COND-MET` | EU | drug | 变更计划（Change Plan） | 基于证据 |
| `DR-CN-PACMP` | CN | drug | 变更计划（Change Plan） | 透明 |
| `DR-CN-SUPPL` | CN | drug | 描述变更（Description of Changes） | 聚焦且有边界 |
| `AU-INTENDED-USE` | UN | auto | 描述变更（Description of Changes） | 聚焦且有边界、基于风险 |
| `AU-INTENDED-USE-REVIEW` | UN | auto | 描述变更（Description of Changes） | 聚焦且有边界 |
| `AU-SUMS-OK` | UN | auto | 影响评估（Impact Assessment） | 全生命周期视角、透明 |
| `AU-SUMS-OUT` | UN | auto | 影响评估（Impact Assessment） | 基于风险、透明 |
| `AU-RXSWIN` | UN | auto | 变更计划（Change Plan） | 透明 |
| `AU-SAFETY` | UN | auto | 描述变更（Description of Changes） | 聚焦且有边界、基于风险 |

## 三、法域分布

| 法域 | 规则 | 叙述 |
|---|---|---|
| US | 9 | 见上表逐条落位 |
| CN | 12 | 见上表逐条落位 |
| EU | 13 | 见上表逐条落位 |

## 四、缺口与结论（按数据写，不按期望写）

- 规则总数 **40**，已映射 **40**，未映射 **0**
- 原则「聚焦且有边界」落点 20 条
- 原则「基于风险」落点 13 条
- 原则「基于证据」落点 9 条
- 原则「透明」落点 10 条
- 原则「全生命周期视角」落点 5 条

注意：本表证明的是**规则可归位**，不是**判定符合 N90**（见 SPEC §9.3 主张边界）。
