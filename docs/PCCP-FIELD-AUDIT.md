# PCCP 字段审计：一个"看起来能用"的字段其实不能用

2026-11-18 · 抽查 2 条，矛盾 1 条 · 原始记录见 `data/pccp_field_audit.json`

## 起因

外面流传的"AI 器械里只有 5.4% 带 PCCP（43/794）"是第三方统计，本仓无法背书。
想自己算，就得找一个**机器可读、权威**的字段。FDA 的 Devices@FDA 页面确实有一个：

> `Predetermined Change Control Plan Authorized`  Yes / No

看起来完美。于是抽查。

## 抽查结果

| 510(k) | 器械名 | 字段值 | summary 原文 | 是否一致 |
|---|---|---|---|---|
| K252041 | Fibresolve (with PCCP) | **Yes** | 第三方转述含 PCCP，允许改架构/训练数据/输入类型 | 一致 |
| K252844 | Tyto Insights for Wheeze Detection (with PCCP) | **No** | "The purpose of this 510(k) submission is to obtain FDA's review and authorization of a **Predetermined Change Control Plan (PCCP)**" | **矛盾** |

K252844 的 summary 里还有一张对比表，第一行就是：

> `PCCP` — `Includes PCCP (submitted for FDA review in this 510(k))`

即：**这次提交的唯一新增内容就是 PCCP**，而 FDA 数据库字段写的是 `No`。

## 结论（可直接对外用的三句）

1. 该字段在 510(k) 记录上**存在漏填**，抽查 2 条即有 1 条矛盾；
2. 因此**任何基于该字段的 PCCP 采用率统计都会偏低**，包括"5.4%"这类数字；
3. 判断某器械是否带 PCCP，**必须回到 summary PDF 原文**，不能只看字段。

## 顺带确认的通道事实

| 通道 | 结果 |
|---|---|
| Shell（urllib / PowerShell）→ accessdata | **404，全站不可达** |
| Agent `web_fetch` → accessdata 详情页 | **通** |
| Agent `web_fetch` → summary PDF | **通**（示例：`pdf25/K252844.pdf` 已实际读到正文） |
| `api.fda.gov` | 通（登记字段，但**不含** PCCP 标记） |

所以"真实 PCCP 回放"的瓶颈不是数据不存在，而是**取数只能走 web_fetch、无法脚本化批量**，
且每条都必须人工读 PDF 编码。这就是为什么本仓至今只做了 2 条，而不是 794 条——
**2 条真读过的，胜过 794 条抄来的。**

## 下一步（要人配合的部分）

1. 选定队列（例如 AI 清单里 decision_date ≥ 2025-08 的全部 510(k)）；
2. 逐条 `web_fetch` summary PDF，人工判读三件事：是否申请 PCCP、变更类型、验证证据；
3. 编码成 `change` 字段喂给 `judge()`，与人工结论对账。

单条约 3–5 分钟，100 条约需 6–8 小时人工。这是唯一能把"结构优势"变成"证据优势"的路。
