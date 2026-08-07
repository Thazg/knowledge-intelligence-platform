# Multi-Query Retrieval Benchmark

## 1. Overview

This report evaluates Multi-Query Retrieval on top of the current hybrid retrieval pipeline.

The objective is to improve retrieval quality by generating multiple semantically equivalent versions of the original user query and retrieving documents for each version.

The final system uses:

- one original query;
- two LLM-generated query rewrites;
- Weighted RRF as the base retriever;
- Multi-Query Reciprocal Rank Fusion;
- document-level deduplication.

The final configuration improves ranking quality over the previous Weighted RRF baseline.

---

## 2. Previous Retrieval Baseline

Before Multi-Query Retrieval, the strongest retrieval strategy was Weighted Reciprocal Rank Fusion.

The baseline pipeline was:

```text
User Query
    ↓
Dense Retrieval
    +
BM25 Retrieval
    ↓
Weighted RRF
    ↓
Document-Level Deduplication
    ↓
Final Top-K
```

### Configuration

```text
Dense model:
BAAI/bge-small-en-v1.5

Sparse retrieval:
BM25

Dense weight:
0.7

BM25 weight:
0.3

RRF constant:
60

Candidate multiplier:
5

Maximum chunks per document:
1
```

### Baseline Performance

| Metric | Weighted RRF |
|---|---:|
| Hit@1 | 0.5455 |
| Hit@3 | 0.9091 |
| Hit@5 | 1.0000 |
| Hit@10 | 1.0000 |
| MRR | 0.7303 |

Weighted RRF therefore served as the baseline for Multi-Query experiments.

---

## 3. Multi-Query Retrieval Architecture

The Multi-Query pipeline expands a single user query into multiple retrieval queries.

```text
User Query
    ↓
Query Rewriter
    ↓
Original Query
Rewrite 1
Rewrite 2
    ↓
Weighted RRF Retrieval
for each query
    ↓
Multi-Query RRF Fusion
    ↓
Document-Level Deduplication
    ↓
Final Top-K
```

The original query is always preserved.

This is important because LLM-generated rewrites may introduce small semantic shifts.

The original query therefore acts as the primary retrieval anchor.

---

## 4. Query Rewriting Model

The query rewriting component uses a local LLM through Ollama.

### Model

```text
qwen3:4b-instruct
```

### Runtime

```text
Ollama
```

### Number of Rewrites

```text
2
```

Each retrieval request therefore produces:

```text
1 original query
+
2 rewritten queries
=
3 total retrieval queries
```

---

## 5. Query Rewriting Prompt

The query rewriter is instructed to:

- preserve the original intent;
- avoid answering the question;
- avoid introducing new facts;
- use concise technical terminology;
- express the same information need differently;
- return exactly two rewrites.

Example:

```text
Original:
How does LangGraph persist state between executions?

Rewrite 1:
How is LangGraph state stored across execution boundaries?

Rewrite 2:
What mechanism does LangGraph use for state persistence between runs?
```

The rewrites are intended to increase semantic and lexical coverage without changing the information need.

---

## 6. Initial Equal-Weight Multi-Query Fusion

The first Multi-Query implementation treated all queries equally.

Query weights:

```text
Original Query = 1.0
Rewrite 1      = 1.0
Rewrite 2      = 1.0
```

For every retrieved chunk, the Multi-Query RRF score was accumulated across query result lists.

Conceptually:

```text
score(chunk)
=
1 / (k + rank_original)
+
1 / (k + rank_rewrite_1)
+
1 / (k + rank_rewrite_2)
```

where:

```text
k = 60
```

Documents that ranked highly for multiple query formulations received stronger fused scores.

---

## 7. Initial Multi-Query Results

An early evaluation produced:

| Metric | Multi-Query |
|---|---:|
| Hit@1 | 0.7273 |
| Hit@3 | 0.7273 |
| Hit@5 | 0.8182 |
| Hit@10 | 1.0000 |
| MRR | 0.7803 |

This initially appeared promising because:

```text
Hit@1:
0.5455 → 0.7273

MRR:
0.7303 → 0.7803
```

However, later runs produced substantially different results.

One subsequent run produced:

```text
Hit@1  = 0.4545
Hit@3  = 0.8182
Hit@5  = 0.8182
Hit@10 = 1.0000
MRR    = 0.6465
```

This revealed a reproducibility problem.

---

## 8. Reproducibility Problem

The original evaluation generated query rewrites dynamically during every benchmark run.

The evaluation flow was:

```text
Evaluation Query
    ↓
Qwen
    ↓
New Rewrites
    ↓
Retrieval
```

Even with a low generation temperature, different runs could produce different query rewrites.

Therefore:

```text
same evaluation query
→ different rewritten queries
→ different retrieval results
→ different benchmark metrics
```

This made the evaluation unreliable.

---

## 9. Deterministic Query Generation

The query rewriter was made more deterministic by configuring generation with:

```text
temperature = 0.0
seed = 42
```

This reduced variation, but deterministic generation alone was not considered sufficient for a reproducible benchmark.

A stronger evaluation design was required.

---

## 10. Frozen Query Rewrites

Query generation was separated from retrieval evaluation.

A dedicated generation script creates rewrites once and stores them in:

```text
backend/evaluation/datasets/query_rewrites.jsonl
```

Example:

```json
{
  "case_id": "langgraph_interrupt_001",
  "original_query": "How do interrupts work in LangGraph?",
  "rewrites": [
    "LangGraph interrupt mechanism during graph execution",
    "How to use interrupts to pause and resume LangGraph execution"
  ]
}
```

The evaluation pipeline no longer calls the LLM.

Instead:

```text
retrieval_cases.jsonl
        +
query_rewrites.jsonl
        ↓
FrozenQueryRewriter
        ↓
Deterministic Retrieval Evaluation
```

This isolates LLM generation from retrieval benchmarking.

---

## 11. Reproducibility Verification

After switching to frozen rewrites, the benchmark was executed twice.

Both runs produced exactly:

```text
Hit@1  = 0.6364
Hit@3  = 0.9091
Hit@5  = 0.9091
Hit@10 = 1.0000
MRR    = 0.7727
```

This confirmed that the benchmark had become reproducible.

The frozen query dataset therefore became part of the retrieval evaluation setup.

---

## 12. Equal-Weight Rank Movement

Using frozen rewrites and equal query weights:

```text
Original = 1.0
Rewrite 1 = 1.0
Rewrite 2 = 1.0
```

the Multi-Query system produced:

```text
Improved : 1
Unchanged: 9
Degraded : 1
```

The improved case was:

```text
langgraph_state_001
Weighted RRF rank: 2
Multi-Query rank : 1
```

The degraded case was:

```text
fastapi_validation_001
Weighted RRF rank: 5
Multi-Query rank : 6
```

This explained the reduction in Hit@5:

```text
Weighted RRF Hit@5 = 1.0000
Multi-Query Hit@5  = 0.9091
```

---

## 13. Weighted Multi-Query Fusion

The equal-weight configuration gave LLM-generated rewrites the same influence as the original query.

This was considered too aggressive.

The original query is the direct representation of the user's information need, while rewrites are generated approximations.

The fusion was therefore changed to:

```text
Original Query = 1.0
Rewrite 1      = 0.7
Rewrite 2      = 0.7
```

The weighted Multi-Query RRF score becomes conceptually:

```text
score(chunk)
=
1.0 / (k + rank_original)
+
0.7 / (k + rank_rewrite_1)
+
0.7 / (k + rank_rewrite_2)
```

This keeps the original query as the strongest retrieval signal while still allowing rewritten queries to improve coverage.

---

## 14. Final Weighted Multi-Query Results

The weighted configuration produced:

| Metric | Weighted Multi-Query |
|---|---:|
| Hit@1 | 0.6364 |
| Hit@3 | 0.9091 |
| Hit@5 | 1.0000 |
| Hit@10 | 1.0000 |
| MRR | 0.7758 |

This is the strongest retrieval result achieved so far.

---

## 15. Final Rank Movement

Compared with Weighted RRF:

```text
Improved : 1
Unchanged: 10
Degraded : 0
```

The only changed case was:

```text
langgraph_state_001
```

Rank movement:

```text
Weighted RRF:
2

Weighted Multi-Query:
1
```

Therefore:

```text
Improvement:
+1 rank
```

No evaluation case was degraded.

---

## 16. Overall Comparison

| Strategy | Hit@1 | Hit@3 | Hit@5 | Hit@10 | MRR |
|---|---:|---:|---:|---:|---:|
| Dense Retrieval | 0.5455 | 0.8182 | 0.9091 | 1.0000 | 0.7197 |
| BM25 | 0.3636 | 0.7273 | 0.9091 | 1.0000 | 0.5842 |
| Equal RRF | 0.3636 | 0.8182 | 1.0000 | 1.0000 | 0.6318 |
| Weighted RRF | 0.5455 | 0.9091 | 1.0000 | 1.0000 | 0.7303 |
| Equal-Weight Multi-Query | 0.6364 | 0.9091 | 0.9091 | 1.0000 | 0.7727 |
| **Weighted Multi-Query** | **0.6364** | **0.9091** | **1.0000** | **1.0000** | **0.7758** |

---

## 17. Improvement Over Weighted RRF

Weighted Multi-Query improves Hit@1 from:

```text
0.5455
```

to:

```text
0.6364
```

This corresponds to one additional query retrieving the expected document at Rank 1.

MRR improves from:

```text
0.7303
```

to:

```text
0.7758
```

Absolute MRR improvement:

```text
+0.0455
```

Relative improvement:

```text
approximately +6.2%
```

At the same time, the system preserves:

```text
Hit@3  = 0.9091
Hit@5  = 1.0000
Hit@10 = 1.0000
```

No evaluation case is degraded relative to Weighted RRF.

---

## 18. Selected Configuration

The best evaluated Multi-Query configuration is:

```text
Query Rewriter:
qwen3:4b-instruct

Runtime:
Ollama

Number of rewrites:
2

Original query weight:
1.0

Rewrite 1 weight:
0.7

Rewrite 2 weight:
0.7

Multi-Query RRF constant:
60

Base retriever:
Weighted RRF

Dense weight:
0.7

BM25 weight:
0.3

Base retrieval candidate multiplier:
5

Maximum chunks per document:
1
```

Evaluation uses frozen rewrites stored in:

```text
backend/evaluation/datasets/query_rewrites.jsonl
```

---

## 19. Retrieval Strategy Decision

Two retrieval configurations are retained.

### Production-Safe Baseline

```text
Weighted RRF
```

Advantages:

- no LLM dependency;
- lower latency;
- deterministic;
- strong retrieval quality;
- simple operational behavior.

Performance:

```text
Hit@1  = 0.5455
Hit@3  = 0.9091
Hit@5  = 1.0000
Hit@10 = 1.0000
MRR    = 0.7303
```

### Best Evaluated Retrieval Strategy

```text
Weighted Multi-Query Retrieval
```

Advantages:

- higher Hit@1;
- higher MRR;
- no degraded evaluation cases;
- preserved Top-5 and Top-10 coverage.

Performance:

```text
Hit@1  = 0.6364
Hit@3  = 0.9091
Hit@5  = 1.0000
Hit@10 = 1.0000
MRR    = 0.7758
```

Weighted Multi-Query is therefore the current best-performing retrieval strategy.

---

## 20. Engineering Findings

### 20.1 Query rewriting can improve retrieval ranking

The rewritten queries provided additional semantic formulations of the same information need.

This helped move:

```text
langgraph_state_001
```

from Rank 2 to Rank 1.

---

### 20.2 The original query should remain the strongest signal

Equal weighting caused one relevant document to move:

```text
Rank 5 → Rank 6
```

Reducing rewrite influence restored the document to the Top 5 while preserving the improvement on the LangGraph state query.

This supports the design principle:

```text
Original query = anchor
Rewrites       = supporting retrieval signals
```

---

### 20.3 LLM-based evaluation inputs must be frozen

Dynamic LLM generation made benchmark results unstable.

Separating:

```text
query generation
```

from:

```text
retrieval evaluation
```

created a deterministic and reproducible benchmark.

This is essential for trustworthy experiment comparison.

---

### 20.4 Higher MRR alone is not sufficient

The initial Multi-Query experiment achieved high MRR but reduced Hit@5.

A retrieval change should therefore be evaluated across multiple metrics.

The final weighted configuration was selected because it improved MRR and Hit@1 without sacrificing Hit@5 or Hit@10.

---

### 20.5 Small weighting changes can materially affect ranking

Changing:

```text
1.0 / 1.0 / 1.0
```

to:

```text
1.0 / 0.7 / 0.7
```

eliminated the only observed regression.

This demonstrates the importance of controlling the influence of generated queries during rank fusion.

---

## 21. Latency Trade-Off

Multi-Query Retrieval requires three retrieval operations:

```text
Original query
Rewrite 1
Rewrite 2
```

instead of one.

It also requires LLM inference when rewrites are generated dynamically in production.

Therefore, compared with Weighted RRF, Multi-Query introduces:

- additional retrieval latency;
- LLM inference latency;
- additional CPU/GPU usage;
- greater operational complexity.

The quality improvement must therefore be evaluated together with latency before final production deployment.

---

## 22. Production Architecture

A practical production design is:

```text
User Query
    ↓
Query Rewriter
qwen3:4b-instruct
    ↓
Original + 2 Rewrites
    ↓
Weighted RRF × 3
    ↓
Weighted Multi-Query RRF
    ↓
Document Deduplication
    ↓
Final Top-K
```

A fallback path should remain available:

```text
Query Rewriter unavailable
        ↓
Weighted RRF
```

This preserves retrieval availability even if the local LLM service is unavailable.

---

## 23. Limitations

The current benchmark contains only 11 active evaluation queries.

This is sufficient for development comparison but not enough to establish broad statistical confidence.

Other limitations include:

- one expected document per query;
- binary relevance;
- limited query diversity;
- no graded relevance judgments;
- no latency benchmark yet;
- no memory or resource benchmark;
- frozen rewrites represent one specific query-generation configuration.

The current results should therefore be interpreted as strong development evidence rather than final production validation.

---

## 24. Future Work

Recommended next experiments include:

1. Expand the evaluation dataset.
2. Add multiple relevant documents per query.
3. Add graded relevance judgments.
4. Measure nDCG.
5. Benchmark end-to-end latency.
6. Measure query rewriting latency separately.
7. Measure retrieval latency separately.
8. Compare one rewrite vs two rewrites.
9. Compare different rewrite weights.
10. Benchmark alternative local query-rewriting models.
11. Introduce query-rewrite caching in production.
12. Detect queries that do not require rewriting.
13. Evaluate adaptive Multi-Query Retrieval.
14. Evaluate Multi-Query Retrieval with cross-encoder reranking.
15. Compare fixed-token and structure-aware chunking.

---

## 25. Conclusion

Multi-Query Retrieval was successfully integrated on top of the Weighted RRF retrieval pipeline.

The initial implementation revealed two important problems:

- dynamic LLM rewrites made evaluation non-reproducible;
- equal weighting gave rewritten queries too much influence.

These issues were addressed by:

- freezing evaluation query rewrites;
- preserving the original query;
- weighting the original query more strongly than generated rewrites.

The final Weighted Multi-Query configuration achieved:

```text
Hit@1  = 0.6364
Hit@3  = 0.9091
Hit@5  = 1.0000
Hit@10 = 1.0000
MRR    = 0.7758
```

Compared with Weighted RRF:

```text
MRR:
0.7303 → 0.7758

Hit@1:
0.5455 → 0.6364

Degraded cases:
0
```

Weighted Multi-Query Retrieval is therefore the current best-performing retrieval strategy in the system.

Weighted RRF remains the production-safe fallback because it provides strong retrieval quality without an LLM dependency.