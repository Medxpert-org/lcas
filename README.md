# LCAS — Change Adjudication Spec

**A deterministic adjudicator for one question regulators actually ask: _is this change still inside
the scope you were approved for?_**

Status: prototype · spec v0.1 · reference implementation v0.2 · Apache-2.0 · 2026-11-18

> ### Read this first
> This repository demonstrates the technical feasibility of encoding multi-jurisdictional change
> adjudication rules as deterministic logic. It has **not** completed rule formalisation,
> tamper-resistant evidence chaining, or validation against real cases, and must **not** be used
> for actual compliance decisions. That scope limit was set by an external review, not by
> self-assessment — see [`REVIEW-LOG.md`](REVIEW-LOG.md).

## The question nothing else answers

Compliance tooling today answers two questions:

- *"Is your documentation complete?"* — document and checklist tools.
- *"Does this model carry risk?"* — AI-governance platforms, which emit risk scores but never a
  decision (Credo AI's own product description: no runtime action at all).

Neither answers the third question. LCAS defines an **output contract** for it, and applies the
same computation across four regimes usually treated as unrelated:

| Domain | Regime | Anchor |
|---|---|---|
| Medical device (AI / software) | PCCP — Predetermined Change Control Plan | FDA PCCP Guidance §V–§VII; 21 CFR 807.81(a)(3) |
| Drug | PACMP — Post-approval Change Management Protocol | ICH Q12 §4; Reg (EU) 2024/1701 |
| Automotive | SUMS + RXSWIN | UN R156 §7.1.1 / §7.1.2.3 / §7.2.1.2.1 |
| General AI | Pre-determined, non-substantial modification | EU AI Act Art.43(4) + Annex IV 2(f) |

Shared structure: **input = change + approved scope; output = in-scope / out-of-scope /
undeterminable, plus the clause that decides it and an offline-recomputable evidence pack.**

## Five verdicts, never a score

`IN_SCOPE` · `NOT_REQUIRED` · `OUT_OF_SCOPE` · `BLOCK` · `UNCERTAIN`

`BLOCK` is the only one that changes *when* rather than *whether*: the change is inside the
approved envelope, but a prerequisite (validation, commitment, record sync) is unmet. It
routes to BLOCK, not to a new submission.

Precedence is fixed and monotone: `OUT_OF_SCOPE > BLOCK > UNCERTAIN > NOT_REQUIRED > IN_SCOPE`.
No voting, no averaging, no "most rules agree, so pass".

`UNCERTAIN` means *route to a human* — never a silent pass. Fail-closed is mandatory, not a setting.

## Measured, not claimed

| Check | Result |
|---|---|
Verdict agreement — 55 cases, 59 jurisdictional judgments, 3 industries, 8 adversarial | 59/59 = 100% |
Safety-direction misses (blocked but passed) — the only metric that must be zero | **0** |
Adversarial cases resisted (prose says "harmless / already approved", fields contradict) | 8/8 |
Exhaustive invariants — 16,480 field combinations → 49,280 judgments, all three domains | 0 violations, deterministic |
Evidence packs re-verified offline | 59/59 MATCH |
Clause anchors audited against primary sources | 36 audited (9 corrected, 7 renumbered, 2 downgraded) · 4 added later, marked `unverified` |

Every number above is produced by a script in this repo. Run it yourself:

```bash
python bench.py                                                       # regression + evidence packs
python -m unittest discover tests -v                                   # contract invariants (fail-closed, traceability)
python fuzz.py                                                        # exhaustive invariants
python release/conformance.py --impl judge.py --check-evidence        # LCAS L2 self-consistency
```

## Run it against your own implementation

```bash
python release/conformance.py --impl /path/to/your_judge.py --check-evidence
```

Loads any module exposing `adjudicate(case)` or `judge(case)`, runs the 55-case set, checks that
each finding carries a clause anchor and a fingerprint, and grades the result L1 / L2.

This tests **consistency with the spec on a self-authored case set**. It does not certify
correctness against any regulator.

## What an external review changed

Four rounds with an independent model (DeepSeek-V4-Pro), receipts kept verbatim in [`reviews/`](reviews/):

1. It found a **real fail-open**: the automotive domain had no rule for "intended use changed", so a
   change with a changed intended use could be judged *not requiring submission* and routed to PASS.
2. Reproduced, then fixed — and it then found our fix **over-blocked** (infotainment-type scope
   expansion), which forced a two-tier rule instead of a blanket block.
3. It also exposed that `fuzz.py` only exhausted the medical domain. Now all three domains are
   exhausted.
4. Finally it capped our claim: with three gaps open (un-formalised trigger thresholds, no rule
   version in the fingerprint, no path from natural-language approval letters to structured scope),
   the honest ceiling is "technical feasibility prototype".

What it did **not** do: make this independently certified. One model, four rounds, is not multiple
independent parties. A second vendor's peer timed out twice and is recorded as failed, not as a pass.

## Still open

- Rule trigger conditions are boolean fields; how a real change form maps onto them is unspecified.
- The evidence fingerprint (`sha256(rule|article|effect)[:12]`) carries no rule version or timestamp,
  so rewriting the rule library and recomputing would still "match".
- Natural-language approved scope cannot yet be structured — this is the blocker for real cases.
- No mechanism for tracking regulation amendments and replaying historical verdicts under an old rule set.
- **Zero real cases.** 55 hand-built samples. The reviewer's standing recommendation: blind-test 20
  real changes with published regulatory outcomes (FDA 510(k) Summaries, EUDAMED).

## Layout

| Path | What |
|---|---|
`SPEC.md` | LCAS-0.1 — verdict model, precedence, evidence pack, fail-closed rules, claim ceiling (§9.1) |
`judge.py` · `domains.py` | Reference implementation, 40 rules across medical / drug / automotive |
`cases.json` | 55-case conformance dataset |
`ANCHORS.md` | Every clause anchor, what was wrong, what it became; `unverified` items flagged |
`REVIEW-LOG.md` · `reviews/` | The external review, verbatim |
`release/` | Conformance kit, rubric, handover sheet, red-team self-report, release checklist |

## License and scope

Apache-2.0 — see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE). Regulatory texts are owned by their
issuing authorities; this repository cites clause numbers and short paraphrases only.
Output is a decision recommendation, never a regulatory conclusion; clinical, legal and regulatory
responsibility stays with the manufacturer or marketing authorisation holder.
