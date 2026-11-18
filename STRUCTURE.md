# STRUCTURE — what lives where, and what breaks if you touch it

LCAS is small on purpose. Everything below is a file in this repository; there is no
hidden layer. Read this before changing anything, because the layers have a one-way
dependency: contract → rules → corpus → harness → governance.

## Layer 1 — Contract

| File | Holds |
|---|---|
| `SPEC.md` | LCAS-0.1: the four verdicts, the priority order, the required input fields, §9.1 claim ceiling, §9.2 multi-jurisdiction action synthesis |

`SPEC.md` is the only place a verdict is allowed to be *defined*. If a rule needs a new
verdict or a new priority relation, the spec changes first, in a separate commit.

## Layer 2 — Rules

| File | Holds |
|---|---|
| `judge.py` | `judge_one(case, jur)`, `judge(case)`; four verdicts `IN_SCOPE` / `NOT_REQUIRED` / `OUT_OF_SCOPE` / `UNCERTAIN`; priority `OUT_OF_SCOPE > BLOCK > UNCERTAIN > NOT_REQUIRED > IN_SCOPE`; per-finding difference attribution |
| `domains.py` | Rule tables per jurisdiction: US (9) / CN (9) / EU (7) for devices, 9 for drugs, 6 for automotive |
| `evidence.py` | Rule → article → effect fingerprint `sha256(rule_id\|article\|effect)[:12]`, so a verdict can be traced to the clause that produced it |

Rules are data, not code paths: a rule is `(id, predicate, verdict, article, effect)`.
Adding a jurisdiction means adding a table, not branching inside `judge.py`.

## Layer 3 — Corpus and extraction

| File | Holds |
|---|---|
| `ANCHORS.md` | 36 clause anchors with disposition: 9 corrected, 7 renumbered, 2 downgraded, 18 confirmed, 4 still `unverified` |
| `data/external_corpus_510k_special_software.json` | 50 frozen FDA 510(k) Special records, fingerprint `98cd507d…91b4b` |
| `data/pilot_texts.json` | 4 real 510(k) narrative excerpts with source URLs |
| `tools/external_corpus_check.py` | Pulls the frozen corpus, recomputes the fingerprint, reports the decidable rate |
| `tools/extract_fields.py` | Deterministic narrative → 11 fields, regex + 60-char negation window, every field carries a quote, abstains instead of guessing |
| `tools/pilot_real_cases.py` | Three-layer report: field coverage / verdicts / agreement with the real outcome label |
| `docs/PILOT-REAL-CASES.md` | What the pilot proved and what it did not |

This layer may *lower* a claim. It is never allowed to raise one: a corpus result can
turn a claim into "not yet measured", never into "measured and good".

## Layer 4 — Harness

| File | Holds | Gate |
|---|---|---|
| `bench.py` | 55 cases, 59 judgments, consistency, offline re-run | must be 59/59 |
| `fuzz.py` | 16,480 combinations over three domains → 49,280 judgments | must be 0 violations, 100 % deterministic |
| `release/conformance.py` | Runs the same cases against any third-party implementation | must report MATCH |
| `.github/workflows/ci.yml` | bench + fuzz + conformance + determinism on 3.10 / 3.12 / 3.13 | must be green |
| `examples/*.json` | Three-state adapter fixtures, exit codes 0 / 1 / 2 | manual + CI |

## Layer 5 — Governance

| File | Holds |
|---|---|
| `EVIDENCE-INDEX.md` | L1 self-reproduction / L2 external review / L3 second implementation / L3.5 external corpus / L4 external node — with the zeros written as zeros |
| `REVIEW-LOG.md`, `reviews/` | Four rounds of external review and the seven changes they forced |
| `ECOSYSTEM.md` | Upstream / complementary / downstream neighbours, and what LCAS explicitly does not do |
| `release/eval/` | RUBRIC, HANDOVER, REPORT-TEMPLATE, MANIFEST — the kit a stranger uses to grade this repo without trusting it |

## Where to make a change, and what it costs

| You want to | Edit | Then re-run | And update |
|---|---|---|---|
| add a clause | `domains.py` + `ANCHORS.md` | `bench.py`, `fuzz.py` | `EVIDENCE-INDEX.md` (anchor count) |
| add a case | `cases.json` | `bench.py` | README measured table |
| change a verdict | `SPEC.md` first, then `judge.py` | all four CI gates | `REVIEW-LOG.md`, README claim ceiling |
| widen the corpus | `data/` + `tools/` | `pilot_real_cases.py` | `docs/PILOT-REAL-CASES.md` |
| raise a claim | `EVIDENCE-INDEX.md` only, and only after the matching level exists | — | README |

A change that skips the "then re-run" column is a change that has not been measured.
