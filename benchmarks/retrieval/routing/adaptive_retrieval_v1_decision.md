# Adaptive Retrieval v1 — Decision Report

## Decision

**Verdict: Do not ship automatic adaptive retrieval in production v1.**

Production v1 will continue to use **Weighted RRF** as the default retrieval strategy.

Higher-cost retrieval strategies remain available for experimentation or explicit use:

- MultiQuery retrieval for coverage-oriented experiments.
- Mixedbread cross-encoder reranking for explicit high-quality retrieval.

Automatic strategy routing is deferred until stronger routing signals and a larger independent evaluation set are available.

---

## Motivation

Adaptive Retrieval v1 was evaluated to determine whether expensive retrieval should be activated only for queries that materially benefit from it.

Three strategies were compared.

### STANDARD

Weighted Reciprocal Rank Fusion:

- Dense weight: 0.7
- BM25 weight: 0.3
- RRF k: 60
- Top K: 10

### COVERAGE

MultiQuery retrieval:

- Original query weight: 1.0
- Rewrite 1 weight: 0.7
- Rewrite 2 weight: 0.7
- Candidate multiplier: 5

### HIGH_QUALITY

Weighted RRF followed by:

- Reranker: `mixedbread-ai/mxbai-rerank-base-v2`
- Candidate pool: 20
- Final Top K: 10

---

## Routing Development Benchmark

The frozen routing development set contains:

- 45 queries
- 391 relevant documents
- 119 relevance-3 documents
- 119 relevance-2 documents
- 153 relevance-1 documents
- Every query has at least one relevance-3 document

### Frozen Ground Truth

SHA256:

`DF1D561F7E4F8D699770F219E7CA5E404AF98CA7704EDD7D53E6966183332341`

### Frozen Query Rewrites

SHA256:

`17AB187DF9761523773D62689FB45A19FCE600C7B2C587D40AE83C3B51F92010`

---

## Strategy Benchmark Results

| Metric | STANDARD | COVERAGE | HIGH_QUALITY |
|---|---:|---:|---:|
| Hit@1 | 0.9111 | 0.9333 | 0.9333 |
| Hit@3 | 0.9778 | 0.9778 | 0.9778 |
| Hit@5 | 0.9778 | 1.0000 | 1.0000 |
| Hit@10 | 1.0000 | 1.0000 | 1.0000 |
| Recall@10 | **0.7635** | 0.7152 | 0.7191 |
| nDCG@10 | 0.7063 | 0.6981 | **0.7292** |
| MRR | 0.9481 | **0.9611** | 0.9600 |
| Mean latency | **206.19 ms** | 650.94 ms | 3874.78 ms |
| P95 latency | **281.23 ms** | 881.10 ms | 4352.34 ms |

Raw benchmark SHA256:

`F31E960AC4F00555AD402BF5896222A4BEBFEF33A5ED5054D8AE6E580310B116`

### Interpretation

Weighted RRF remained highly competitive in retrieval quality while being substantially faster.

Compared with STANDARD:

- COVERAGE was about 3.2× slower.
- HIGH_QUALITY was about 18.8× slower.
- HIGH_QUALITY improved nDCG@10 but reduced Recall@10.
- COVERAGE slightly improved MRR but reduced Recall@10 and nDCG@10.

Neither expensive strategy justified global activation.

---

## Empirical Preferred Strategies

A predeclared promotion policy was applied to per-query benchmark results.

Final empirical strategy labels:

- STANDARD: 34 / 45 — 75.6%
- COVERAGE: 2 / 45 — 4.4%
- HIGH_QUALITY: 9 / 45 — 20.0%
- Expensive-path rate: 24.4%

Preferred-strategy artifact SHA256:

`813B0223DBA2F1C811680A95BC3799E45BD51894653519EA7F82E3CA405C1B9C`

This showed that most queries did not benefit enough from expensive retrieval to justify escalation.

---

## Router Experiments

### Query-Only Features

Candidate runtime-visible features included:

- Multiple technologies
- Explicit constraints
- Runtime/lifecycle wording
- Integration/connection wording
- Broad enumeration wording

No individual query feature reliably separated STANDARD from HIGH_QUALITY cases.

### Dense/BM25 Agreement

Runtime retrieval diagnostics were also evaluated:

- Top-1 agreement
- Document overlap@3
- Document overlap@5
- Document overlap@10
- Jaccard overlap

HIGH_QUALITY queries showed somewhat lower Dense/BM25 agreement on average.

For example:

- STANDARD Jaccard@10: 0.230
- HIGH_QUALITY Jaccard@10: 0.141

However, distributions overlapped substantially.

Some STANDARD queries had zero Dense/BM25 overlap, while some HIGH_QUALITY queries showed relatively strong agreement.

Retrieval disagreement alone was therefore insufficient for routing.

---

## Combined Signal Experiment

The final experiment combined query-level complexity signals with retrieval disagreement.

The strongest tested rule was:

```text
(multi_technology OR explicit_constraint)
AND
document_overlap_at_10 <= 2
```

Results:

- True positives: 6
- False positives: 3
- True negatives: 31
- False negatives: 3
- Precision: 0.667
- Recall: 0.667
- False-positive rate: 0.088
- Activation rate: 0.209

Combined-signal audit SHA256:

`CAD4247F42096F24A8C8A2B40AA26A2D72CBC1C10D5F0B9489EA0AE2408F0440`

---

## Why Auto-Routing Was Rejected

HIGH_QUALITY retrieval costs approximately 19× more latency than STANDARD.

A routing precision of 66.7% means roughly one third of automatic reranker activations would be unnecessary.

This was considered too expensive for production v1.

Continuing to tune thresholds or add more heuristics on the same 45-case development set would also create a significant risk of overfitting.

The safer production policy is:

```text
Uncertain
    ↓
STANDARD
```

---

## Production v1 Decision

### Default Retrieval

**Weighted RRF**

### MultiQuery

Supported experimentally, but not automatically activated.

### Mixedbread Reranker

Supported as an explicit high-quality retrieval mode, but not automatically activated.

### Adaptive Router

**Not shipped in v1.**

Adaptive routing can be reconsidered when:

- More routing evaluation cases are available.
- A separate holdout routing set exists.
- Stronger runtime confidence signals are identified.
- Automatic escalation achieves substantially higher precision.

---

## Engineering Takeaway

Adaptive Retrieval v1 produced a useful negative result.

The experiments showed that additional retrieval complexity should not be shipped solely because it improves isolated quality metrics.

Weighted RRF currently provides the strongest quality-latency trade-off for production v1, while the available routing signals are not reliable enough to justify automatic expensive-path activation.
