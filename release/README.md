# LCAS-0.1 — Change Adjudication Spec & Conformance Kit

**Status:** draft v0.1 (spec) / v0.2 (reference implementation) · Apache-2.0 · 2026-11-18

## The gap this fills

Compliance tooling answers two questions today:

- *"Is your documentation complete?"* — document/checklist tools.
- *"Does this model carry risk?"* — AI governance platforms (risk scores, never decisions).

Neither answers the question a regulator actually asks:

> **"Is this change still inside the scope you were approved for?"**

LCAS defines the output contract for that third question. The same computation covers four
regimes that are usually treated as unrelated:

| Domain | Regime | Anchor |
|---|---|---|
| Medical device (AI/software) | PCCP — Predetermined Change Control Plan | FDA PCCP Guidance §V–§VII; 21 CFR 807.81(a)(3) |
| Drug | PACMP — Post-approval Change Management Protocol | ICH Q12 §4 |
| Automotive | SUMS + RXSWIN | UN R156 §7.1.1 / §7.1.2.3 / §7.2.1.2.1 |
| General AI | Predetermined, non-substantial modification | EU AI Act Art.43(4) + Annex IV 2(f) |

Shared structure — **input: change + approved scope; output: in-scope / out-of-scope / undeterminable,
with the clause that decides it and an offline-recomputable evidence pack.**

## Four verdicts, never a score

`IN_SCOPE` · `NOT_REQUIRED` · `OUT_OF_SCOPE` · `UNCERTAIN`

Precedence is fixed and monotone: `OUT_OF_SCOPE > BLOCK > UNCERTAIN > NOT_REQUIRED > IN_SCOPE`.
`UNCERTAIN` means *route to a human* — never a silent pass. Fail-closed is mandatory, not a setting.

## What has actually been measured

| Check | Result |
|---|---|
Verdict agreement (55 cases, 59 jurisdictional judgments, 3 industries incl. 8 adversarial) | **59/59 = 100%** |
Safety-direction misses (blocked-but-passed) — the only metric that must be zero | **0** |
Adversarial cases resisted (description claims "harmless / already approved", fields contradict) | **8/8** |
Exhaustive invariants (16,480 field combinations → 49,280 judgments, all three domains) | **0 violations**, deterministic |
Evidence packs re-verified offline | **59/59 = MATCH** |
Clause anchors audited against primary sources | 36 anchors: 9 corrected, 7 renumbered, 2 downgraded, 18 confirmed · **4 anchors added after external review are marked `unverified`** |

## Claim ceiling

An independent external review (DeepSeek-V4-Pro, 2026-11-18, four rounds — receipts in
`review_test/reviews/`) concluded that three gaps remain open: rule trigger conditions are not
formalised into enumerable thresholds; the evidence fingerprint carries no rule version or
timestamp; natural-language approved scope has no structuring path.

On that basis we adopt the reviewer's wording verbatim as our own ceiling, and do **not** claim more:

> This system demonstrates the technical feasibility of encoding multi-jurisdictional change
> adjudication rules as deterministic logic. It has **not** completed rule formalisation,
> tamper-resistant evidence chaining, or validation against real cases, and must **not** be used
> for actual compliance decisions.

What follows from that: the "third-party conformance kit" here tests **internal consistency**
against a self-authored case set. It does not, and cannot yet, certify correctness against
regulators. See `REVIEW-LOG.md` for what the external review changed and what it left open.


## Quick start

```bash
python bench.py                                  # regression + evidence packs
python fuzz.py                                   # exhaustive invariants
python release/conformance.py --impl judge.py --check-evidence   # LCAS L2
```

Run the whole suite against **your own** implementation instead of ours:

```bash
python release/conformance.py --impl ./your_judge.py --check-evidence
```

Your module exposes either `adjudicate(case) -> {jurisdiction: verdict}` or
`judge(case) -> {"results": {...}}`. The kit reports verdict conformance and evidence fields.
L3 additionally requires an offline-recomputable evidence pack (not machine-checkable here).

## Layout

| Path | Content |
|---|---|
`SPEC.md` | Normative spec (Chinese is the authoritative text) |
`ANCHORS.md` | Clause-anchor audit trail, including the corrections we had to make |
`judge.py` / `domains.py` | Reference implementation, device + drug + automotive rule libraries |
`cases.json` | 55-case conformance dataset (expected verdicts hand-labelled from the regulations) |
`fuzz.py` | Exhaustive invariant test |
`evidence.py` | Canonical JSON + SHA-256 evidence pack and offline verification |
`bench-report.html` | Generated scorecard (numbers computed, not written) |

## Non-goals

Not a compliance conclusion. Not a substitute for the manufacturer's legal responsibility.
No accuracy claim — only **reproducibility**: same input, same implementation, same output, and a
readable reason. Uncovered scenarios return `UNCERTAIN` by design.

## License

Apache-2.0, matching the `lgd-engine` repository this implementation is integrated into.

---

*Maintained by LGD. The point is not to be convenient to adopt, but to make it impossible to claim
you are doing "change adjudication" without meeting the contract.*
