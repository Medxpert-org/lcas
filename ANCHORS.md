# 法条锚核验表 · ANCHORS v2

> 2026-11-18（二稿）｜ 覆盖 40 条规则的全部法条锚 ｜ 核验口径：能否在一手文本里定位到该条
> **状态：40 条全部处置完毕 —— 9 条错锚已改 · 7 条编号补正 · 2 条依据不足已降级 · 18 条已核 · 待核 0**
> 一稿曾标 6 条"待核"；本轮全部取到一手原文，其中 2 条实为**引用不成立**，已降级而非硬留。

## 为什么必须做这件事

"每条裁决都带法条锚"是这个项目唯一不可替代的卖点，也是它最大的风险点：
锚错了，整套输出的可信度归零。竞品给风险分不需要锚，我们给了锚就必须负责。

---

## A. 错锚已改（9 条，一稿）

| 规则 | 原锚（错） | 改为 | 一手证据 |
|---|---|---|---|
US-PCCP-R1 | Guidance §III | §V Policy + 21 CFR 807.81(a)(3) | 指南正文 V. Policy for PCCPs |
US-PCCP-R2 | §IV.A Planned Modifications | §VI Description of Modifications | 指南正文（Section VI） |
US-PCCP-R3 | §IV.B Modification Protocol（边界） | §VI（范围界定）+ §VII | 同上 |
US-PCCP-R4 | §IV.C Impact Assessment | §VII Modification Protocol（预定义接受准则） | 指南正文（Section VII） |
US-PCCP-OK | §V Implementation | §V（经授权 PCCP 内实施无需新提交） | 同上 |
AU-SUMS-OK | §7 SUMS | §7.1.1（SUMS 过程）+ §7.2.1.2.1 | EUR-Lex 42021X0388 |
AU-SUMS-OUT | **§7.5**（不存在） | §7.2.1.2.1（导致批准扩展/新批准须更新 RXSWIN） | 同上 |
AU-RXSWIN | **§7.6**（不存在） | §7.1.2.3（可审计登记册） | 同上 |
AU-SAFETY | §7 + UN R155/**R13H** | §7.1.1 + UN R155（网络安全） | 去掉无据的 R13H |

---

## B. 编号/称谓补正（7 条，本轮）

| 规则 | 原写 | 改为 | 依据 |
|---|---|---|---|
DR-PACMP-IN / OUT / ABSENT / COND-MET | ICH Q12 **§2.2** | ICH Q12 **§4**（4.1 定义 / 4.2 应用 / 4.3 要素 / 4.4 已批准 PACMP 的修改 / 4.5 类型） | EMA Q12 Step 5 目录：第 4 章即 PACMP |
CN-INTENDED-USE | "NMPA 2021 年第 47 号" | 《医疗器械注册与备案管理办法》（**市场监管总局令第 47 号**，2021-08-26 公布，2021-10-01 施行） | 市场监管总局原文：是总局令，不是 NMPA 公告 |
DR-CN-PACMP | "NMPA 2025 年第 119 号公告" | 国家药监局 2025 年第 119 号公告（PACMP 国内可用；配套 2023 年第 108 号） | 药监局官网原文（2025-12-12 发布） |
US-SW-Q3 | Q3 | **Q3a/Q3b**（新增或修改危险/风险控制） | 510(k) 软件变更指南正文确为编号问答，Q3 分 a/b 支 |

> Q1（仅网络安全加固）、Q2（仅把系统恢复到规格内）经原文核对**成立**，未改。

---

## C. 依据不足，已降级（2 条，本轮）

| 规则 | 原锚 | 问题 | 处理 |
|---|---|---|---|
EU-CYBER-MINOR | MDCG 2019-16 网络安全指南；MDR Art.120 | MDCG 2019-16 是网络安全**要求**文件，不能直接支撑"非显著即不需 NB" | 锚收敛为 `MDR Art.120 + MDCG 2019-16（网络安全要求）` |
EU-PERF-TUNE | MDR Art.52 + NBOG BPG 2014-3 | 该 BPG 针对 QMS 变更，非器械变更 | 删去 BPG，锚收敛为 `MDR Art.52（符合性评估程序）` |

**这两条仍可用，但只在"制造商内部评估"这一层，不可用于对外声称"法规明确豁免 NB"。**

---

## D. 已核，可与公开原文对上（18 条）

21 CFR 807.81(a)(3)；FDA PCCP 指南 §V–§VII；UN R156 §7.1.1 / §7.1.2.3 / §7.2.1.2.1 / §7.2.1.2.2；510(k) 软件变更指南 Q1 / Q2 / Q3a / Q3b；
EU AI Act Art.43(4) + Annex IV 2(f)；MDR Art.2(1) / Art.52 / Art.120 / Annex VIII；
NMPA 2025 年第 63 号公告；深度学习辅助决策软件审评要点（二）；ICH Q12 §4；2025 年第 119 号公告；市场监管总局令第 47 号。

---

## 一手来源

1. FDA PCCP 指南正文（含 Section VI / VII 编号）：https://pathologyinnovationcc.org/s/FDA1_Guidance-Predetermined-Change-Control-AIML-copy.pdf
2. UN R156（EUR-Lex 42021X0388）：https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:42021X0388
3. UN R156 修订提案（§7.1.1.3 / §7.1.2.3 逐条原文）：https://www.unece.org/sites/default/files/2020-12/ECE-TRANS-WP29-GRVA-2021-06e.pdf
4. 510(k) 软件变更指南（HHS 全文，Q1/Q2/Q3a/Q3b）：https://www.hhs.gov/guidance/sites/default/files/hhs-guidance-documents/FDA/1500055.pdf
5. ICH Q12 Step 5（PACMP = 第 4 章）：https://www.ema.europa.eu/documents/scientific-guideline/ich-guideline-q12-technical-regulatory-considerations-pharmaceutical-product-lifecycle-management_en.pdf
6. 市场监管总局令第 47 号：https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/fgs/art/2023/art_568880e3ee344c45b38d073bba1c53ad.html
7. 国家药监局 2025 年第 119 号公告：https://www.nmpa.gov.cn/directory/web/nmpa/xxgk/ggtg/ypggtg/ypqtggtg/20251217175129135.html
8. IMDRF N90《Essential Principles and Content of PCCPs》：https://www.imdrf.org/sites/default/files/2026-08/IMDRF%20SaMD%20WG%20N90%20FINAL%20Essential%20Principles%20and%20Content%20PCCPs%20(1).pdf

---

## 修正后复跑（2026-11-18）

| 指标 | 结果 |
|---|---|
判定一致率 | 59/59 = 100% |
安全方向漏判 | 0 |
不变量违例 | 0 / 49,280 判定 |
规则加载 | 引擎侧 25 条（医械），全库 40 条 |
引擎侧 `--domain pccp` | REJECT，exit=2（行为不变） |

> 锚点改动只影响"依据写在哪"，不影响判定逻辑——这正是要修的原因：
> 结论对、依据写错，在真实审计里等同于结论错。

---

## 三稿追加（2026-11-18 晚）：外审发现 fail-open 后新增的 3 条锚

外部评审（DeepSeek-V4-Pro，R02）指出：汽车与药品两域缺"预期用途改变"规则，
导致一个预期用途已变的变更可被判为"不需申报"而放行。已复现并修复，新增 3 条规则。
**这 3 条锚尚未做一手原文核验，按 SPEC §3 一律标记 `unverified`，不得用于对外结论。**

| # | 规则 | 引用条款 | 状态 | 说明 |
|---|---|---|---|---|
1 | `AU-INTENDED-USE` | UN R156 §7.1.1 + §7.2.1.2.1 | `unverified` | 功能/用途范围扩展应走批准扩展，但"新增自动驾驶功能等级"是否明确落在 §7.2.1.2.1 需核原文 |
2 | `DR-INTENDED-USE` | Directive 2001/83/EC Art.19；Reg (EU) 2024/1701（Type II） | `unverified` | "适应症变更＝Type II 变更"的判断需核 2024/1701 附件分类清单 |
3 | `DR-CN-INTENDED-USE` | 《药品注册管理办法》补充申请事项 | `unverified` | 需核该办法中"增加适应症"对应的具体条款号 |

> 处置要求：外发前必须把上述 3 条补进一手核验，或降级为 `UNCERTAIN`（进人工）。
> 在此之前，这两域的"预期用途改变"结论只能作为**保守拦截**使用，不得作为合规依据引用。

