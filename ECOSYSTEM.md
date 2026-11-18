# ECOSYSTEM — LCAS 的上下游与互补位

> 参照 `zhaoxinghua09-cell/uibc-core` 的排法：先给五层地图，再给可执行的互动，最后明说哪条是空的。
> 本文件只描述**位置与接口**，不宣称任何一家的认可。

## 一、五层地图

| 层 | LCAS 在这里是什么 | 落地物 |
|---|---|---|
规范 | 「变更是否超出已批准范围」的输出契约 | `SPEC.md`（LCAS-0.1，含 §9.1 主张上限）|
实现 | 40 条规则、三行业三法域的确定性判定器 | `judge.py` · `domains.py` |
工具 | 任何人可跑的一致性检验 | `release/conformance.py` · `tools/external_corpus_check.py` |
验证 | 自测、穷举、对抗、外审 | `fuzz.py` · `release/REDTEAM.md` · `reviews/` |
存证 | 证据包 + 语料指纹 | `evidence.py` · `data/…json` 的 sha256 |

三条阅读路线：
- 只想知道能不能用 → `README.md` 的 Claim ceiling → 停。
- 想验证我们有没有吹 → `REVIEW-LOG.md` → `reviews/` → 自己跑 `bench.py`。
- 想接进自己系统 → `SPEC.md §4`（证据包）→ `release/HANDBOOT.md`。

## 二、上游（喂给 LCAS 的）

| 上游 | 给的是什么 | 接法 |
|---|---|---|
**lgd-theory** | 理论 SSOT（三律、有籍有证有门禁） | 只引不改；理论文本版权归原作者 |
**uibc-core** | registry / evidence / gates 的可执行原语，含 sigstore 与外部节点分级 | **最该对齐的一个**：LCAS 的证据包应复用它的存证原语，而不是自造指纹 |
FDA openFDA | 真实 510(k) 记录（含 Special 类型的变更申报）| 已接：`tools/external_corpus_check.py` |
EMA / 欧盟 variation 库 | 药品变更分类（IA/IB/II）与真实变更类型 | 未接 |
UNECE DETA | R156 批准扩展与 RXSWIN 记录 | 未接 |
法规文本 | FDA 指南、21 CFR、ICH Q12、MDR/AI Act、NMPA 公告、UN R156 | 已接：`ANCHORS.md`（36 条已核 / 4 条 `unverified`）|

## 三、互补（相邻但不抢同一件事，可以互动）

| 项目 | 它做的那半 | LCAS 补的另一半 |
|---|---|---|
**sigstore / Rekor / in-toto** | 签名的不可否认与透明日志 | 我们只证"同一输入同一输出"，证不了"当时的规则版本"——**这是外审指出的第 2 号缺口，解法就在这里** |
**CycloneDX / SPDX（SBOM）** | 软件成分与版本的事实记录 | 变更判定需要"改了什么"，SBOM diff 正好提供结构化事实 |
OpenTimestamps（你们已在 uibc-core 用）| 时间锚定 | 补"何时判的" |
**medharness / dhfkit** | DHF 结构与审批门（文档侧）| 判定侧没人做，我们不重复它的门 |
NeMo Guardrails / Antihero | 拦模型说了什么（运行时）| 不涉法规条文，我们不重复它的拦截 |
Credo AI / OneTrust | 风险评分与治理台账 | 只给分不给决定，我们给四值裁决 |
Greenlight Guru | 器械 QMS 的 traceability 与预测性检查 | 不做"是否必须提交"的裁决 |

**结论一句**：真正值得对接的是 **sigstore 系存证** 与 **SBOM**——前者补我们最弱的一环，后者给我们最缺的结构化输入；其余四家是相邻赛道，交叉引用即可，不必谈集成。

## 四、下游（会消费 LCAS 的）

| 下游 | 怎么用 |
|---|---|
CI/CD 门禁（GitHub Actions）| 变更 PR 合并前打一次判定，`OUT_OF_SCOPE` 直接卡住发布 |
eQMS 变更控制流程 | 变更单提交时自动附一份裁决与依据，供 RA 复核 |
RA 提交准备 | 判定为 OUT_OF_SCOPE 时，直接给出"该走哪条路径"与条款依据 |
公告机构 / 审评侧（远期）| 作为"制造商自评是否成立"的可复核材料，**不是**替代审评 |

## 五、同门兄弟（都在你自己的生态里，别互相打架）

| 仓 | 关系 |
|---|---|
`lgd-theory` | 理论 SSOT，LCAS 只消费不生产 |
`uibc-core` | 协议与存证原语；LCAS 是它在**法规判定**这一垂直面上的应用 |
`lgd-engine` | 13→14 域引擎，LCAS 已作为 `--domain pccp` 接入（`exit 0/1/2` 实测）|
`LGD` | 对外入口与贡献者系统 |
`uibc-competition` | 竞赛/对照场，可作为第三方实现的测试床 |
`lcas`（本仓）| 规范 + 参考实现 + 符合性工具 |

## 六、本周可做的三种互动（都不需要联系外人）

1. **已做**：外部语料检验 —— 用 openFDA 真实 510(k) 当"别人的语料"，结果 **0/50 可判定**
   （语料指纹 `98cd507d…`）。这个 0 不是失败，是把"没有抽取层"这个缺口量化了。
2. **可做**：与 `uibc-core` 共用存证原语 —— 把 `evidence.py` 的指纹换成
   `sha256(rule_version|article|effect|timestamp)` + 可选 in-toto 证明，让"改库重算"失效。
3. **可做**：把 `tools/external_corpus_check.py` 的语料指纹写进 README，
   让别人能确认"你测的是同一批 50 条"。

## 七、明确不做

- 不在别人的仓里开 issue 推销（除非对方先问）；
- 不把"引用链接"说成"合作"；
- 不因为相邻产品做过一点相似的事就改自己的定位。
