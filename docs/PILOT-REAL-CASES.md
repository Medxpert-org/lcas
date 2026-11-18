# PILOT — 真实案例试点（4 份 FDA 510(k) 原文）

> 目的：验证"没有真实案例"能不能拆成两个可分别解决的问题——**抽得出字段吗**，**抽出来能判吗**。
> 结果：前者部分成立（22.7%），后者仍为 0。结论不好看，但是真数字。

## 方法与可复现

```bash
python tools/pilot_real_cases.py
```

- 语料：4 份 FDA 510(k) 原文摘录（`data/pilot_texts.json`，含每条来源 URL）
- 抽取：`tools/extract_fields.py` —— 纯正则 + 否定窗口，**不调模型**，每条字段必须附原文引语
- 判定：`judge()`，`--domain medical`，US 法域
- 标签：**后果标签**——这 4 条都是 FDA 实际受理并审过的变更申报，即"该变更被当作需提交的变更处理"

## 结果

| 记录 | 类型 | 抽出字段 | 判定 | 与后果标签一致 |
|---|---|---|---|---|
K132338 | Special | 2/11 | UNCERTAIN | 否 |
K240553 | Traditional | 1/11 | UNCERTAIN | 否 |
K243540 | Special | 4/11 | UNCERTAIN | 否 |
K251463 | Special | 3/11 | UNCERTAIN | 否 |

- 字段覆盖率 **22.7%**（平均 2.5/11）
- 可判定率 **0/4**
- 与后果标签一致 **0/4**

抽出来的字段本身是对的，且带引语，例如：

- `new_intended_use=False` ← "INDICATION/INTENDED USE … HAS NOT CHANGED"（FDA 备忘录标准句）
- `architecture_change=False` ← "fundamental scientific technology has not changed"
- `new_output=True` ← "introduces … a new version of the EP amplifier"
- `introduces_new_risk=False` ← "No new questions of safety or effectiveness were raised"
- `acceptance_met=True` ← "met their respective acceptance criteria"

## 这证明了什么

1. **真实文书里确实有可判定的结构化信号**，且集中在固定句式上——FDA 的 Special 510(k) 备忘录几乎是一个模板，抽取可行性高于预期；
2. **缺口不是"读不懂文本"，而是"字段不够 + 规则没接上"**：11 个字段只覆盖了 5 类，而 FDA 807(b) 真正的判据是"是否可能显著影响安全有效性"，这个字段目前抽不出来；
3. 更有意思的矛盾：**FDA 受理了这些变更，同时申请人文书写着"不影响安全有效性"**。这说明"不影响"不等于"不需提交"——而我们现有规则恰好把"not significant"推向 `NOT_REQUIRED`。**这是规则层的语义错误，不是数据问题**。

## 这没证明什么

- 不能证明"抽取准确率 22.7%"（只有 4 份，且摘录是人工挑的）；
- 不能证明规则错在哪一条——只证明"not significant → NOT_REQUIRED"这条链在真实案例上会失配；
- 后果标签 ≠ 规范标签：FDA 受理不代表"规范上必须提交"，两者不能混。

## 下一步（按性价比排序）

1. **扩样本到 20 份**（同一脚本，换 `--limit`），先看覆盖率是不是稳定在 20–30%；
2. **补 3 个字段**：`affects_safety_effectiveness`、`submission_type`（Special/Traditional）、`change_scope`（软件/硬件/标签）；
3. **重写 `US-807` 触发条件**：把"not significant → 不需提交"降级为"仅在明确说明不影响安全有效性、且变更类型属 Q1/Q2 时"，其余一律 `UNCERTAIN`；
4. 3 做完再跑同一批 20 份，看「与后果标签一致」能不能从 0 起来——这才是唯一能对外说的进步。
