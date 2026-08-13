# Adaptive Retrieval Routing Development Set

## Purpose

This directory contains the development/tuning dataset for Adaptive Retrieval v1.

It is intentionally separate from the canonical 100-case retrieval benchmark.

Use this set to explore routing patterns, tune deterministic routing rules, inspect routing mistakes, and compare per-query utility across retrieval strategies.

## Current Distribution

```text
STANDARD      20
COVERAGE      12
HIGH_QUALITY  13
----------------
TOTAL         45
```

## Routing Labels

### STANDARD

Hypothesis: use the default Weighted RRF path.

Typical characteristics:
- clear intent;
- narrow single-tool lookup;
- specific terminology;
- no obvious need for expensive retrieval expansion.

### COVERAGE

Hypothesis: the query may benefit from Multi-Query retrieval.

Typical characteristics:
- broad or underspecified intent;
- multiple plausible formulations;
- several related concepts may contain useful evidence;
- recall/coverage may matter more than first-result precision.

### HIGH_QUALITY

Hypothesis: the query may justify Weighted RRF + Cross-Encoder reranking.

Typical characteristics:
- cross-tool reasoning;
- several technical constraints;
- precision-sensitive evidence selection;
- a wrong high-ranked document could materially degrade the final answer.

## Important: Labels Are Hypotheses

`initial_label` is not final routing ground truth.

Each development query should eventually be run through all candidate strategies:

```text
STANDARD
-> Weighted RRF

COVERAGE
-> Multi-Query

HIGH_QUALITY
-> Weighted RRF + Mixedbread v2
```

The preferred strategy should be derived from measured per-query utility rather than from the initial human label alone.

## Anti-Leakage Rules

The canonical evaluation set is:

```text
benchmarks/retrieval/cases.jsonl
```

Do not tune the router using outcomes from the canonical 100 cases.

Development cases must:
1. use unique case IDs;
2. not copy canonical queries;
3. not intentionally paraphrase canonical queries;
4. remain separate from canonical evaluation;
5. be used only for router design/tuning until the router is frozen.

All current records are `status = "draft"`.

Before tuning, compare all 45 queries against the full local `cases.jsonl` and remove or rewrite exact or near-duplicate cases.

## Evaluation Principle

Compare at least these four systems:

```text
Always Weighted RRF
Always Multi-Query
Always Mixedbread v2 reranking
Adaptive Router
```

Adaptive Retrieval should only be shipped if it provides a useful system-level trade-off across:
- MRR;
- Recall@K;
- nDCG@K;
- expensive-path activation rate;
- mean retrieval latency;
- P95 retrieval latency.

The goal is to selectively pay for expensive retrieval only when it produces measurable value.
