# Cross-Encoder Reranker Benchmark

## 1. Overview

This report compares multiple cross-encoder reranking models on top of the
current Weighted Reciprocal Rank Fusion retrieval pipeline.

The objective is to determine whether any evaluated reranker improves the
existing retrieval baseline.

Models evaluated:

1. `cross-encoder/ms-marco-MiniLM-L6-v2`
2. `cross-encoder/ms-marco-MiniLM-L12-v2`
3. `mixedbread-ai/mxbai-rerank-base-v1`

All models were evaluated using the same:

- retrieval pipeline;
- candidate-pool strategy;
- document deduplication;
- passage representation;
- evaluation dataset.

This keeps the comparison focused on the reranker model itself.

---

## 2. Baseline Retrieval Pipeline

The current retrieval pipeline is:

```text
User Query
    ↓
Dense Retrieval
    +
BM25 Retrieval
    ↓
Weighted Reciprocal Rank Fusion
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

RRF constant:
60

Dense weight:
0.7

BM25 weight:
0.3

Candidate multiplier:
5

Maximum chunks per document:
1
```

---

## 3. Evaluation Setup

Evaluation cases:

```text
11
```

Metrics:

- Hit@1
- Hit@3
- Hit@5
- Hit@10
- Mean Reciprocal Rank (MRR)

Each evaluation case currently contains one expected document.

Because there is only one expected document per query, Hit@K is numerically
equivalent to Recall@K in the current benchmark.

---

## 4. Weighted RRF Baseline

Weighted RRF performance:

| Metric | Weighted RRF |
|---|---:|
| Hit@1 | 0.5455 |
| Hit@3 | 0.9091 |
| Hit@5 | 1.0000 |
| Hit@10 | 1.0000 |
| MRR | 0.7303 |

This is the reference baseline that a reranker must outperform.

---

## 5. Reranking Pipeline

The evaluated reranking pipeline is:

```text
User Query
    ↓
Weighted RRF Retrieval
    ↓
Top Candidate Documents
    ↓
Cross-Encoder Reranker
    ↓
Final Top-K
```

Reranker candidate configuration:

```text
Candidate multiplier: 2
Maximum chunks per document: 1
```

---

## 6. Reranker Passage Representation

All final model comparisons use the following candidate representation:

```text
Title: <document title>
Source: <documentation source>
Path: <relative document path>
Content: <chunk content>
```

The cross-encoder receives:

```text
(query, enriched passage)
```

This representation was selected after the initial reranking experiment
showed that content-only inputs produced substantially weaker results.

---

## 7. Model 1 — MiniLM-L6-v2

### Model

```text
cross-encoder/ms-marco-MiniLM-L6-v2
```

### Results

| Metric | MiniLM-L6-v2 |
|---|---:|
| Hit@1 | 0.4545 |
| Hit@3 | 0.9091 |
| Hit@5 | 1.0000 |
| Hit@10 | 1.0000 |
| MRR | 0.6591 |

### Analysis

MiniLM-L6 preserved strong Top-5 and Top-10 coverage, but reduced:

```text
Hit@1
MRR
```

compared with Weighted RRF.

The model therefore did not improve the current default ranking strategy.

---

## 8. Model 2 — MiniLM-L12-v2

### Model

```text
cross-encoder/ms-marco-MiniLM-L12-v2
```

### Results

| Metric | MiniLM-L12-v2 |
|---|---:|
| Hit@1 | 0.5455 |
| Hit@3 | 0.9091 |
| Hit@5 | 1.0000 |
| Hit@10 | 1.0000 |
| MRR | 0.7197 |

### Analysis

MiniLM-L12 substantially outperformed MiniLM-L6.

Its Hit@K values matched the Weighted RRF baseline exactly:

```text
Hit@1  = 0.5455
Hit@3  = 0.9091
Hit@5  = 1.0000
Hit@10 = 1.0000
```

However:

```text
Weighted RRF MRR = 0.7303
MiniLM-L12 MRR   = 0.7197
```

The difference is:

```text
0.0106
```

MiniLM-L12-v2 is the strongest reranker tested, but it still does not exceed
the baseline.

---

## 9. Model 3 — mxbai-rerank-base-v1

### Model

```text
mixedbread-ai/mxbai-rerank-base-v1
```

### Results

| Metric | mxbai-rerank-base-v1 |
|---|---:|
| Hit@1 | 0.4545 |
| Hit@3 | 0.9091 |
| Hit@5 | 0.9091 |
| Hit@10 | 0.9091 |
| MRR | 0.6667 |

### Analysis

The model underperformed both Weighted RRF and MiniLM-L12.

Most importantly:

```text
Hit@10 = 0.9091
```

This means at least one expected document that existed in the hybrid
candidate ranking was moved outside the final Top 10.

For a RAG pipeline, losing relevant evidence after successful first-stage
retrieval is undesirable.

---

## 10. Overall Benchmark

| Strategy / Model | Hit@1 | Hit@3 | Hit@5 | Hit@10 | MRR |
|---|---:|---:|---:|---:|---:|
| Weighted RRF | **0.5455** | **0.9091** | **1.0000** | **1.0000** | **0.7303** |
| MiniLM-L6-v2 | 0.4545 | 0.9091 | 1.0000 | 1.0000 | 0.6591 |
| MiniLM-L12-v2 | **0.5455** | **0.9091** | **1.0000** | **1.0000** | 0.7197 |
| mxbai-rerank-base-v1 | 0.4545 | 0.9091 | 0.9091 | 0.9091 | 0.6667 |

---

## 11. Ranking

Based on retrieval quality:

```text
1. Weighted RRF
2. MiniLM-L12-v2
3. mxbai-rerank-base-v1
4. MiniLM-L6-v2
```

For reranker-only selection:

```text
1. MiniLM-L12-v2
2. mxbai-rerank-base-v1
3. MiniLM-L6-v2
```

MiniLM-L12-v2 is therefore retained as the strongest experimental reranker.

---

## 12. Key Findings

### 12.1 The strongest system does not currently use a reranker

Weighted RRF achieved the highest MRR:

```text
0.7303
```

No tested reranker exceeded this value.

This demonstrates that additional pipeline complexity does not
automatically improve retrieval quality.

---

### 12.2 Model selection matters

The difference between MiniLM-L6 and MiniLM-L12 is substantial:

```text
MiniLM-L6 MRR  = 0.6591
MiniLM-L12 MRR = 0.7197
```

Both belong to the same model family, yet their ranking performance differs
significantly.

Reranker selection must therefore be benchmark-driven.

---

### 12.3 Larger or newer models are not automatically better

`mxbai-rerank-base-v1` did not outperform MiniLM-L12 on the current
technical-documentation benchmark.

Model size or recency alone is not sufficient for selecting a reranker.

---

### 12.4 Strong first-stage retrieval reduces reranker headroom

Weighted RRF already combines:

- semantic relevance;
- lexical relevance;
- rank fusion;
- document diversification.

The reranker therefore receives a relatively strong candidate ordering.

In such a system, the reranker must make only highly reliable ranking
changes. Incorrect promotions can easily reduce MRR.

---

### 12.5 Retrieval coverage is more important than reranking sophistication

Weighted RRF maintains:

```text
Hit@5  = 1.0000
Hit@10 = 1.0000
```

This ensures the correct document is consistently available to downstream
RAG components.

A reranker that reduces this coverage is not acceptable as a default
component.

---

## 13. Selected Default Strategy

The default retrieval strategy remains:

```text
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

Selected configuration:

```text
Embedding model:
BAAI/bge-small-en-v1.5

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

Performance:

```text
Hit@1  = 0.5455
Hit@3  = 0.9091
Hit@5  = 1.0000
Hit@10 = 1.0000
MRR    = 0.7303
```

---

## 14. Reranker Decision

### Default Pipeline

Do not apply cross-encoder reranking.

Use:

```text
Weighted RRF
```

as the final retrieval ranking.

### Experimental Reranker

Retain:

```text
cross-encoder/ms-marco-MiniLM-L12-v2
```

for future experiments.

### Current Non-Selected Models

```text
cross-encoder/ms-marco-MiniLM-L6-v2
mixedbread-ai/mxbai-rerank-base-v1
```

are not selected for the current default configuration.

---

## 15. Limitations

The current benchmark contains only 11 queries.

This evaluation size is suitable for development experiments but is not
large enough to make strong general claims about retrieval quality.

The ground truth also currently assumes one expected document per query.

Potential issues include:

- multiple documents may correctly answer the same query;
- an alternative relevant document may be treated as incorrect;
- relevance is evaluated primarily at document level;
- cross-encoders rank individual chunks;
- relevance is currently binary rather than graded.

---

## 16. Future Work

Future reranker evaluation should include:

1. Expand the retrieval evaluation dataset.
2. Add multiple relevant documents per query.
3. Introduce graded relevance judgments.
4. Measure nDCG.
5. Measure reranker latency.
6. Measure CPU and GPU memory usage.
7. Compare rerankers using Markdown-aware chunks.
8. Evaluate reranking after semantic chunking.
9. Benchmark reranking after query rewriting.
10. Benchmark reranking after multi-query retrieval.
11. Evaluate domain-specific technical-documentation rerankers.
12. Compare quality-versus-latency trade-offs.

---

## 17. Conclusion

Three cross-encoder rerankers were evaluated on top of the Weighted RRF
retrieval pipeline.

MiniLM-L12-v2 was the strongest reranker tested and nearly matched the
Weighted RRF baseline.

However, none of the evaluated rerankers improved the baseline MRR.

The current system therefore prioritizes empirical retrieval quality over
additional architectural complexity.

Weighted RRF remains the default retrieval strategy, while MiniLM-L12-v2 is
retained as an experimental reranker for future evaluation after other
retrieval components are improved.