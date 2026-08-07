# Cross-Encoder Reranker Benchmark

## 1. Overview

This report evaluates several cross-encoder reranking models on top of the current hybrid retrieval pipeline.

The purpose of this experiment is to determine whether a reranker can improve the ranking quality of the existing Weighted Reciprocal Rank Fusion (RRF) baseline.

The current hybrid retrieval pipeline combines:

- dense vector retrieval;
- BM25 lexical retrieval;
- Weighted Reciprocal Rank Fusion;
- document-level deduplication.

The reranker is applied only after hybrid retrieval produces a candidate set.

---

## 2. Baseline Retrieval Pipeline

The baseline retrieval strategy is Weighted RRF.

### Configuration

- Dense retriever: `BAAI/bge-small-en-v1.5`
- Sparse retriever: BM25
- Vector database: Qdrant
- Similarity metric: cosine similarity
- RRF constant: 60
- Dense weight: 0.7
- BM25 weight: 0.3
- Candidate multiplier: 5
- Maximum chunks per document: 1
- Evaluation cases: 11

### Baseline Metrics

| Metric | Weighted RRF |
|---|---:|
| Hit@1 | 0.5455 |
| Hit@3 | 0.9091 |
| Hit@5 | 1.0000 |
| Hit@10 | 1.0000 |
| MRR | 0.7303 |

Weighted RRF is therefore used as the reference baseline for all reranker experiments.

---

## 3. Reranking Pipeline

The reranking pipeline is:

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
Final Top-K Results
```

The cross-encoder evaluates each pair:

```text
(query, candidate passage)
```

and assigns a relevance score.

Candidates are then sorted by the cross-encoder score.

---

## 4. Reranker Input Representation

The initial reranker implementation used only chunk content:

```text
(query, chunk.content)
```

This produced weak evaluation results.

The passage representation was therefore expanded to include metadata:

```text
Title: <document title>
Source: <source name>
Path: <relative path>
Content: <chunk content>
```

This improved the reranker's ability to identify the semantic role of technical documentation pages.

The final reranker input includes:

- title;
- source;
- relative path;
- chunk content.

---

## 5. Candidate Pool Configuration

The first reranking experiment used a larger candidate pool.

This caused the reranker to reorder too many relatively weak candidates.

The candidate multiplier was therefore reduced.

Final configuration:

```text
Reranker candidate multiplier: 2
Maximum chunks per document: 1
```

For example, when the final evaluation requests:

```text
Top-K = 10
```

the reranker receives approximately:

```text
20 hybrid candidates
```

and returns the final Top 10.

---

## 6. Model 1: MiniLM-L6-v2

### Model

```text
cross-encoder/ms-marco-MiniLM-L6-v2
```

This model was used as the initial reranking baseline.

### Initial Result

Before metadata enrichment and candidate-pool adjustment:

| Metric | MiniLM-L6-v2 |
|---|---:|
| Hit@1 | 0.2727 |
| Hit@3 | 0.7273 |
| Hit@5 | 0.9091 |
| Hit@10 | 1.0000 |
| MRR | 0.5236 |

This result significantly underperformed the Weighted RRF baseline.

### Improved Configuration

After:

- adding title, source, and path metadata;
- reducing reranker candidate multiplier;

the metrics improved to:

| Metric | MiniLM-L6-v2 |
|---|---:|
| Hit@1 | 0.4545 |
| Hit@3 | 0.9091 |
| Hit@5 | 1.0000 |
| Hit@10 | 1.0000 |
| MRR | 0.6591 |

### Analysis

The improvements show that reranker input representation and candidate-pool size have a substantial effect on performance.

However, the model still underperformed Weighted RRF at:

- Hit@1;
- MRR.

---

## 7. Rank Movement Analysis

The MiniLM-L6-v2 reranker was compared directly against Weighted RRF for each evaluation query.

### Summary

| Movement | Cases |
|---|---:|
| Improved | 1 |
| Unchanged | 7 |
| Degraded | 3 |

### Observed Changes

| Evaluation Case | Hybrid Rank | Reranked Rank | Result |
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

The reranker preserved the original ranking for most queries but degraded more queries than it improved.

---

## 8. Model 2: MiniLM-L12-v2

### Model

```text
cross-encoder/ms-marco-MiniLM-L12-v2
```

This model uses a deeper MiniLM architecture than the L6 baseline.

All retrieval and evaluation settings were kept unchanged.

### Results

| Metric | MiniLM-L12-v2 |
|---|---:|
| Hit@1 | 0.5455 |
| Hit@3 | 0.9091 |
| Hit@5 | 1.0000 |
| Hit@10 | 1.0000 |
| MRR | 0.7197 |

### Analysis

MiniLM-L12-v2 substantially outperformed MiniLM-L6-v2.

It recovered all Hit@K metrics to the same level as Weighted RRF:

```text
Hit@1  = 0.5455
Hit@3  = 0.9091
Hit@5  = 1.0000
Hit@10 = 1.0000
```

However, MRR remained slightly below the Weighted RRF baseline:

```text
Weighted RRF MRR = 0.7303
MiniLM-L12 MRR   = 0.7197
```

The difference is:

```text
0.0106
```

MiniLM-L12-v2 is therefore the strongest reranker evaluated in this experiment, but it does not outperform the baseline.

---

## 9. Model 3: mxbai-rerank-base-v1

### Model

```text
mixedbread-ai/mxbai-rerank-base-v1
```

The same retrieval candidate set and evaluation configuration were used.

### Results

| Metric | mxbai-rerank-base-v1 |
|---|---:|
| Hit@1 | 0.4545 |
| Hit@3 | 0.9091 |
| Hit@5 | 0.9091 |
| Hit@10 | 0.9091 |
| MRR | 0.6667 |

### Analysis

This model performed better than the original MiniLM-L6-v2 baseline in MRR, but worse than MiniLM-L12-v2 and Weighted RRF.

The most important regression was:

```text
Hit@10 = 0.9091
```

This means at least one expected document was pushed outside the Top 10 after reranking.

For a RAG system, reducing Top-K coverage is undesirable because downstream generation can no longer access evidence that was successfully retrieved by the hybrid retriever.

---

## 10. Overall Model Comparison

| Strategy / Model | Hit@1 | Hit@3 | Hit@5 | Hit@10 | MRR |
|---|---:|---:|---:|---:|---:|
| Weighted RRF | **0.5455** | **0.9091** | **1.0000** | **1.0000** | **0.7303** |
| MiniLM-L6-v2 | 0.4545 | 0.9091 | 1.0000 | 1.0000 | 0.6591 |
| MiniLM-L12-v2 | **0.5455** | **0.9091** | **1.0000** | **1.0000** | 0.7197 |
| mxbai-rerank-base-v1 | 0.4545 | 0.9091 | 0.9091 | 0.9091 | 0.6667 |

---

## 11. Key Findings

### 11.1 Reranking is highly model-dependent

The three rerankers produced noticeably different results despite receiving the same candidate set.

MiniLM-L12-v2 performed significantly better than MiniLM-L6-v2.

This confirms that simply adding a cross-encoder does not guarantee better retrieval quality.

---

### 11.2 Metadata improves reranker input quality

Using only chunk content produced substantially weaker results.

Adding:

- title;
- source;
- relative path;

provided additional document-level context and improved ranking quality.

This is particularly important for technical documentation, where titles and paths contain strong semantic signals.

---

### 11.3 Candidate-pool size matters

Reranking a large number of candidates increased the probability that the cross-encoder would promote weaker candidates.

Reducing the candidate multiplier improved stability.

This demonstrates an important trade-off:

```text
larger candidate pool
→ potentially higher recall
→ more reranking noise
→ higher latency
```

versus:

```text
smaller candidate pool
→ more focused reranking
→ lower latency
→ potentially more stable ranking
```

---

### 11.4 Weighted RRF remains highly competitive

The Weighted RRF baseline already combines:

- semantic retrieval;
- lexical retrieval;
- rank fusion;
- document diversification.

As a result, the candidate ranking is already strong before reranking.

The reranker therefore has relatively little room for improvement and can easily degrade a good initial ranking.

---

### 11.5 Larger rerankers are not automatically better

`mxbai-rerank-base-v1` did not outperform the smaller MiniLM-L12 model on the current benchmark.

Model size alone is therefore not a sufficient selection criterion.

Reranker selection should be based on measured retrieval quality, latency, and operational cost.

---

## 12. Selected Retrieval Strategy

The current default retrieval pipeline remains:

```text
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

Selected configuration:

```text
Embedding model: BAAI/bge-small-en-v1.5

Dense weight: 0.7
BM25 weight: 0.3

RRF constant: 60

Candidate multiplier: 5
Maximum chunks per document: 1
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

## 13. Reranker Selection

Among the evaluated cross-encoder models, the strongest reranker is:

```text
cross-encoder/ms-marco-MiniLM-L12-v2
```

Performance:

```text
Hit@1  = 0.5455
Hit@3  = 0.9091
Hit@5  = 1.0000
Hit@10 = 1.0000
MRR    = 0.7197
```

Although its Hit@K metrics match Weighted RRF, its MRR remains slightly lower.

For this reason, reranking is currently classified as an:

```text
experimental retrieval component
```

rather than part of the default retrieval pipeline.

---

## 14. Decision

### Default

Use:

```text
Weighted RRF
```

without cross-encoder reranking.

### Experimental

Retain:

```text
cross-encoder/ms-marco-MiniLM-L12-v2
```

for future experiments.

### Rejected for Current Default

Do not use:

```text
cross-encoder/ms-marco-MiniLM-L6-v2
mixedbread-ai/mxbai-rerank-base-v1
```

as default rerankers based on the current benchmark.

---

## 15. Limitations

The current benchmark contains only 11 evaluation queries.

The results are sufficient for comparing implementations during development, but they are not sufficient to establish general retrieval quality across the entire knowledge base.

The current evaluation also uses one expected document per query.

This creates several limitations:

- multiple valid documents may exist for the same query;
- an alternative relevant document may be incorrectly treated as non-relevant;
- document-level relevance does not guarantee that every chunk from the document is equally useful;
- rerankers operate at chunk level while the current ground truth is primarily document-level.

Future evaluation should support multiple relevant documents and graded relevance.

---

## 16. Future Work

Recommended future experiments include:

1. Expand the evaluation dataset beyond 11 queries.
2. Add multiple relevant documents per query.
3. Introduce graded relevance judgments.
4. Measure nDCG in addition to Hit@K and MRR.
5. Benchmark reranker latency.
6. Measure CPU/GPU memory usage.
7. Evaluate rerankers on Markdown-aware chunks.
8. Compare fixed-token and semantic chunking.
9. Test domain-specific reranking models.
10. Re-evaluate reranking after query rewriting and multi-query retrieval are implemented.

---

## 17. Conclusion

Cross-encoder reranking was successfully integrated and evaluated as a second-stage ranking component.

The experiments demonstrated that reranking performance depends strongly on:

- model selection;
- input representation;
- candidate-pool size;
- the quality of the initial retrieval ranking.

MiniLM-L12-v2 was the strongest reranker tested, but it still did not outperform the existing Weighted RRF baseline.

Therefore, Weighted RRF remains the default retrieval strategy for the current system.

Cross-encoder reranking remains an experimental component that may become more valuable after future improvements to chunking, query rewriting, candidate generation, and evaluation quality.