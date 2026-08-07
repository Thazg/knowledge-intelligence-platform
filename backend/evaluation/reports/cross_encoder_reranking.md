# Cross-Encoder Reranking Experiment

> **Status:** Experimental analysis.
>
> This report documents the initial cross-encoder reranking experiment using
> `cross-encoder/ms-marco-MiniLM-L6-v2`.
>
> For the final multi-model comparison and reranker selection decision, see
> `reranker_benchmark.md`.

## 1. Objective

The purpose of this experiment is to evaluate whether a cross-encoder
reranker can improve the ranking produced by the current Weighted Reciprocal
Rank Fusion (RRF) retrieval pipeline.

The existing retrieval pipeline already combines:

- dense semantic retrieval;
- BM25 lexical retrieval;
- Weighted Reciprocal Rank Fusion;
- document-level deduplication.

The reranker is introduced as a second-stage ranking component:

```text
User Query
    ↓
Dense Retrieval
    +
BM25 Retrieval
    ↓
Weighted RRF
    ↓
Candidate Documents
    ↓
Cross-Encoder Reranker
    ↓
Final Top-K
```

The main evaluation objective is to improve:

- Hit@1;
- Mean Reciprocal Rank (MRR);

while preserving:

- Hit@3;
- Hit@5;
- Hit@10.

---

## 2. Weighted RRF Baseline

The current default retrieval configuration is:

```text
Dense model: BAAI/bge-small-en-v1.5
Sparse retrieval: BM25

Dense weight: 0.7
BM25 weight: 0.3

RRF constant: 60
Candidate multiplier: 5
Maximum chunks per document: 1
```

Evaluation dataset:

```text
11 queries
```

Baseline performance:

| Metric | Weighted RRF |
|---|---:|
| Hit@1 | 0.5455 |
| Hit@3 | 0.9091 |
| Hit@5 | 1.0000 |
| Hit@10 | 1.0000 |
| MRR | 0.7303 |

This is the reference point for evaluating reranking performance.

---

## 3. Initial Reranker

The first cross-encoder evaluated was:

```text
cross-encoder/ms-marco-MiniLM-L6-v2
```

The reranker scores pairs of:

```text
(query, candidate passage)
```

and sorts candidates according to the predicted relevance score.

---

## 4. Initial Passage Representation

The first implementation passed only the chunk content to the reranker:

```text
(query, chunk.content)
```

The resulting performance was:

| Metric | Initial MiniLM-L6 Reranking |
|---|---:|
| Hit@1 | 0.2727 |
| Hit@3 | 0.7273 |
| Hit@5 | 0.9091 |
| Hit@10 | 1.0000 |
| MRR | 0.5236 |

This was substantially worse than the Weighted RRF baseline.

The result suggested that the reranker did not receive enough document-level
context to distinguish between semantically similar technical passages.

---

## 5. Metadata-Enriched Passage Representation

Technical documentation contains useful relevance signals outside the chunk
body itself.

The reranker input was therefore expanded to include:

- title;
- source;
- relative path;
- chunk content.

The final passage representation became:

```text
Title: <document title>
Source: <source>
Path: <relative path>
Content: <chunk content>
```

Example:

```text
Title: BuildKit
Source: docker
Path: content/manuals/build/buildkit/_index.md
Content: BuildKit is the builder backend used by Docker...
```

This provides the reranker with additional document-level context.

---

## 6. Candidate Pool Adjustment

The initial reranking pipeline also used a relatively large candidate pool.

A larger candidate pool can improve coverage, but it also:

- increases inference latency;
- introduces more weak candidates;
- gives the reranker more opportunities to disturb an already strong ranking.

The reranker candidate multiplier was therefore reduced.

Final experimental configuration:

```text
Reranker candidate multiplier: 2
Maximum chunks per document: 1
```

For example:

```text
Final Top-K = 10
        ↓
Hybrid candidates = 20
        ↓
Cross-Encoder
        ↓
Final Top 10
```

---

## 7. Improved MiniLM-L6 Results

After metadata enrichment and candidate-pool reduction:

| Metric | Weighted RRF | MiniLM-L6 Reranked |
|---|---:|---:|
| Hit@1 | 0.5455 | 0.4545 |
| Hit@3 | 0.9091 | 0.9091 |
| Hit@5 | 1.0000 | 1.0000 |
| Hit@10 | 1.0000 | 1.0000 |
| MRR | 0.7303 | 0.6591 |

Compared with the initial reranking experiment:

```text
MRR: 0.5236 → 0.6591
```

This demonstrates that both passage representation and candidate-pool size
have a substantial effect on reranking performance.

However, the reranker still underperformed Weighted RRF in:

- Hit@1;
- MRR.

---

## 8. Rank Movement Analysis

To understand where reranking helped or hurt, the expected document rank was
compared before and after reranking.

### Summary

| Movement | Cases |
|---|---:|
| Improved | 1 |
| Unchanged | 7 |
| Degraded | 3 |

### Detailed Results

| Evaluation Case | Hybrid Rank | Reranked Rank | Movement |
|---|---:|---:|---|
| `docker_cache_001` | 2 | 3 | Degraded |
| `docker_dockerignore_001` | 3 | 3 | Unchanged |
| `kubernetes_configmap_001` | 1 | 1 | Unchanged |
| `kubernetes_liveness_001` | 1 | 1 | Unchanged |
| `fastapi_background_tasks_001` | 1 | 2 | Degraded |
| `fastapi_middleware_001` | 1 | 1 | Unchanged |
| `fastapi_validation_001` | 5 | 3 | Improved |
| `langgraph_checkpoint_001` | 1 | 1 | Unchanged |
| `langgraph_interrupt_001` | 2 | 2 | Unchanged |
| `langgraph_state_001` | 2 | 4 | Degraded |
| `langgraph_memory_001` | 1 | 1 | Unchanged |

The reranker preserved the existing rank for most queries, but degraded more
cases than it improved.

---

## 9. Findings

### 9.1 The reranker implementation is functioning correctly

A synthetic unit test confirmed that the cross-encoder correctly promotes a
highly relevant passage above unrelated candidates.

The poor benchmark result is therefore not caused by:

- model loading;
- inference;
- sorting;
- rank assignment.

The issue is retrieval-quality related rather than implementation related.

---

### 9.2 Metadata materially improves reranking

Adding document metadata increased MRR from:

```text
0.5236
```

to:

```text
0.6591
```

This suggests that technical-documentation reranking benefits from
information such as:

- page title;
- documentation source;
- document path.

---

### 9.3 Candidate-pool size affects ranking stability

Reranking too many candidates can degrade a strong first-stage ranking.

Reducing the candidate pool improved stability and reduced unnecessary
reranker influence.

---

### 9.4 Reranking does not automatically improve retrieval

The Weighted RRF baseline is already strong.

A second-stage model must therefore outperform a relatively high-quality
candidate ordering rather than correcting a weak retriever.

This makes reranking gains harder to achieve.

---

## 10. Decision

The MiniLM-L6 reranker should not replace Weighted RRF as the default ranking
strategy.

Current default:

```text
Weighted RRF
```

Experimental component:

```text
cross-encoder/ms-marco-MiniLM-L6-v2
```

The next step is to benchmark stronger reranker models under the same
retrieval and evaluation configuration.

---

## 11. Limitations

The current evaluation contains only 11 queries.

The dataset also contains one expected document per query, while several
queries may have multiple valid answers.

The reranker operates on individual chunks, whereas the evaluation ground
truth is currently document-oriented.

These limitations should be addressed in future retrieval evaluation work.

---

## 12. Conclusion

The initial cross-encoder experiment demonstrated that reranking quality is
highly sensitive to:

- passage representation;
- candidate-pool size;
- model choice.

Metadata enrichment and candidate-pool reduction substantially improved the
MiniLM-L6 reranker.

However, the final result remained below the Weighted RRF baseline.

For this reason, MiniLM-L6 remains an experimental reranker rather than part
of the default retrieval pipeline.