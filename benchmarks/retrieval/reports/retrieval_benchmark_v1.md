# Retrieval Benchmark v1

## 1. Overview

This benchmark evaluates retrieval quality across **100 manually verified canonical evaluation cases**.

The benchmark contains five categories:

- Semantic: 20 cases
- Lexical: 20 cases
- Ambiguous: 20 cases
- Version-specific: 20 cases
- Cross-tool: 20 cases

**Total: 100 cases**

Each case may contain multiple relevant documents with graded relevance:

- `3` = highly relevant
- `2` = relevant
- `1` = partially relevant

This report focuses on **retrieval quality only**. Operational latency and the final production deployment decision are documented separately in `retrieval_latency_v1.md`.

---

## 2. Retrieval Strategies

The following retrieval strategies were evaluated:

1. Dense Retrieval
2. BM25
3. Weighted Reciprocal Rank Fusion (Weighted RRF)
4. Multi-Query Retrieval
5. Weighted RRF + Cross-Encoder Reranking

### 2.1 Dense Retrieval

Dense Retrieval uses:

- Embedding model: `BAAI/bge-small-en-v1.5`
- Vector database: Qdrant
- Canonical collection: `enterprise_knowledge_fixed_bge_small`

### 2.2 BM25

BM25 provides sparse lexical retrieval over the same canonical chunk corpus used by Dense Retrieval.

### 2.3 Weighted RRF

Weighted Reciprocal Rank Fusion combines Dense and BM25 rankings.

Configuration:

- Dense weight: `0.7`
- BM25 weight: `0.3`
- RRF k: `60`

### 2.4 Multi-Query Retrieval

Multi-Query Retrieval expands the original query into multiple rewritten queries.

Frozen query rewrites are used during evaluation to keep the benchmark deterministic and reproducible.

### 2.5 Cross-Encoder Reranking

Cross-Encoder reranking is applied on top of Weighted RRF candidates.

The canonical reranker model-comparison protocol uses:

- Base retriever: Weighted RRF
- Final `top_k`: `10`
- Candidate multiplier: `4`
- Candidate pool: up to `40`
- Maximum chunks per document: `1`
- Batch size: `16`
- Passage representation: title + source + path + content

Five reranker models were compared under this fixed protocol.

After model selection, the strongest reranker was also evaluated with a smaller candidate multiplier of `2`, corresponding to a candidate pool of up to `20`.

---

## 3. Evaluation Metrics

The benchmark evaluates retrieval quality using:

- Hit@1
- Hit@3
- Hit@5
- Hit@10
- Recall@3
- Recall@5
- Recall@10
- nDCG@3
- nDCG@5
- nDCG@10
- Mean Reciprocal Rank (MRR)

**Hit@K** measures whether at least one relevant document appears within the top K results.

**Recall@K** measures how much of the relevant document set is retrieved within the top K results.

**nDCG@K** evaluates ranking quality while accounting for graded relevance and result position.

**MRR** measures how early the first relevant document appears in the ranking.

---

## 4. Overall Retrieval Quality

| Retriever | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Recall@3 | Recall@5 | Recall@10 | nDCG@3 | nDCG@5 | nDCG@10 | MRR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Dense | 0.5300 | 0.7700 | 0.8200 | 0.8900 | 0.6225 | 0.7025 | 0.7958 | 0.5697 | 0.6000 | 0.6364 | 0.6644 |
| BM25 | 0.4700 | 0.7100 | 0.8000 | 0.8700 | 0.5317 | 0.6250 | 0.7308 | 0.4844 | 0.5257 | 0.5650 | 0.6083 |
| Weighted RRF | 0.6200 | **0.8100** | 0.8700 | 0.9300 | 0.6408 | 0.7308 | 0.8392 | 0.6010 | 0.6402 | 0.6788 | 0.7247 |
| Multi-Query | 0.5800 | **0.8100** | **0.8800** | 0.9500 | 0.6358 | **0.7658** | 0.8425 | 0.6007 | 0.6565 | 0.6830 | 0.7137 |
| **Reranked Hybrid — Mixedbread v2, pool 20** | **0.6700** | **0.8100** | 0.8700 | **0.9700** | **0.6675** | 0.7558 | **0.8758** | **0.6414** | **0.6800** | **0.7276** | **0.7564** |

The strongest retrieval-quality configuration evaluated is:

```text
Weighted RRF
    |
    v
Top 20 Candidates
    |
    v
mixedbread-ai/mxbai-rerank-base-v2
    |
    v
Final Top 10
```

Weighted RRF remains the strongest non-reranked global baseline, while Mixedbread v2 reranking produces the best overall offline retrieval quality.

---

## 5. Cross-Encoder Model Benchmark

### 5.1 Objective

The original reranking experiment used `cross-encoder/ms-marco-MiniLM-L12-v2` and reduced retrieval quality relative to Weighted RRF.

Rather than concluding that Cross-Encoder reranking itself was ineffective, a controlled model-selection benchmark was performed.

All five reranker models were evaluated on the same 100 canonical cases using the same retrieval protocol and a 40-candidate reranking pool.

Only the reranker model changed.

### 5.2 Models Evaluated

1. `cross-encoder/ms-marco-MiniLM-L6-v2`
2. `cross-encoder/ms-marco-MiniLM-L12-v2`
3. `mixedbread-ai/mxbai-rerank-base-v1`
4. `BAAI/bge-reranker-v2-m3`
5. `mixedbread-ai/mxbai-rerank-base-v2`

### 5.3 Model-Selection Results

| Reranker | Hit@1 | Hit@5 | Hit@10 | Recall@10 | nDCG@10 | MRR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| MiniLM-L6-v2 | 0.5600 | 0.7800 | 0.8400 | 0.7367 | 0.6124 | 0.6488 |
| MiniLM-L12-v2 | 0.5300 | 0.8000 | 0.9200 | 0.7858 | 0.6268 | 0.6461 |
| mxbai-rerank-base-v1 | 0.5400 | 0.8800 | 0.9100 | 0.8042 | 0.6558 | 0.6792 |
| BGE-reranker-v2-m3 | 0.5600 | 0.8600 | 0.9200 | 0.7875 | 0.6527 | 0.6693 |
| **mxbai-rerank-base-v2** | **0.6600** | **0.8800** | **0.9500** | **0.8525** | **0.7156** | **0.7475** |

Reference Weighted RRF baseline:

```text
Hit@1      = 0.6200
Hit@5      = 0.8700
Hit@10     = 0.9300
Recall@10  = 0.8392
nDCG@10    = 0.6788
MRR        = 0.7247
```

`mxbai-rerank-base-v2` was the **only evaluated reranker model that improved the overall Weighted RRF baseline** under the 40-candidate model-comparison protocol.

This demonstrates that Cross-Encoder reranking is highly model-dependent.

---

## 6. Candidate-Pool Quality Ablation

The model-comparison benchmark used up to 40 reranking candidates (`candidate_multiplier=4`).

Because `mxbai-rerank-base-v2` was the only reranker to improve the Weighted RRF baseline, a focused quality ablation compared:

```text
candidate_multiplier = 4
40 candidates

vs

candidate_multiplier = 2
20 candidates
```

All other settings remained unchanged.

| Configuration | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Recall@10 | nDCG@10 | MRR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Weighted RRF baseline | 0.6200 | 0.8100 | 0.8700 | 0.9300 | 0.8392 | 0.6788 | 0.7247 |
| Mixedbread v2 — pool 40 | 0.6600 | 0.7900 | **0.8800** | 0.9500 | 0.8525 | 0.7156 | 0.7475 |
| **Mixedbread v2 — pool 20** | **0.6700** | **0.8100** | 0.8700 | **0.9700** | **0.8758** | **0.7276** | **0.7564** |

Reducing the candidate pool from 40 to 20 improved the major overall quality metrics:

- Hit@1: `0.6600 -> 0.6700`
- Hit@10: `0.9500 -> 0.9700`
- Recall@10: `0.8525 -> 0.8758`
- nDCG@10: `0.7156 -> 0.7276`
- MRR: `0.7475 -> 0.7564`

The result suggests that the additional candidates in ranks 21-40 introduced more ranking noise than useful evidence for this reranker on the canonical corpus.

More reranking candidates therefore did not automatically improve retrieval quality.

---

## 7. Category MRR

| Category | Dense | BM25 | Weighted RRF | Multi-Query | Mixedbread v2 — pool 20 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ambiguous | 0.4183 | 0.2681 | 0.4592 | 0.5319 | **0.6097** |
| Cross-tool | 0.5671 | **0.6308** | 0.6181 | 0.5972 | 0.6073 |
| Lexical | 0.7363 | 0.6660 | 0.8792 | 0.8517 | **0.9292** |
| Semantic | 0.7083 | 0.7000 | 0.8088 | 0.8000 | **0.8142** |
| Version-specific | **0.8917** | 0.7767 | 0.8583 | 0.7875 | 0.8217 |

The best-performing strategy differs by query category:

| Category | Best Strategy | MRR |
| --- | --- | ---: |
| Ambiguous | Mixedbread v2 reranking | 0.6097 |
| Cross-tool | BM25 | 0.6308 |
| Lexical | Mixedbread v2 reranking | 0.9292 |
| Semantic | Mixedbread v2 reranking | 0.8142 |
| Version-specific | Dense | 0.8917 |

No single retrieval strategy is best for every query type.

---

## 8. Retrieval-Strategy Findings

### 8.1 Dense Retrieval

Dense Retrieval provides a strong semantic baseline.

It performed particularly well on version-specific queries:

- Version-specific MRR: `0.8917`
- Version-specific Hit@1: `0.8500`
- Version-specific Recall@3: `0.9250`
- Version-specific nDCG@3: `0.8578`

Dense Retrieval was substantially weaker on ambiguous queries:

- Ambiguous MRR: `0.4183`
- Ambiguous Hit@1: `0.3000`
- Ambiguous Recall@10: `0.5250`
- Ambiguous nDCG@10: `0.3672`

Dense semantic similarity alone is therefore not sufficient for underspecified queries.

### 8.2 BM25

BM25 achieved lower overall performance than Dense Retrieval:

- Dense MRR: `0.6644`
- BM25 MRR: `0.6083`

However, BM25 contributes useful lexical signals and is especially competitive for cross-tool retrieval:

- BM25 cross-tool MRR: `0.6308`
- Dense cross-tool MRR: `0.5671`

BM25 therefore remains valuable as a complementary first-stage retriever.

### 8.3 Weighted RRF

Weighted RRF is the strongest non-reranked global baseline.

Compared with Dense Retrieval:

- Hit@1 improved from `0.5300` to `0.6200`.
- MRR improved from `0.6644` to `0.7247`.
- Recall@10 improved from `0.7958` to `0.8392`.
- nDCG@10 improved from `0.6364` to `0.6788`.

Lexical MRR:

- Dense: `0.7363`
- BM25: `0.6660`
- Weighted RRF: `0.8792`

Semantic MRR:

- Dense: `0.7083`
- BM25: `0.7000`
- Weighted RRF: `0.8088`

These results show that Dense and BM25 provide complementary ranking signals that become more effective when fused.

### 8.4 Multi-Query Retrieval

Multi-Query improves evidence coverage.

Overall:

- Hit@5: `0.8800`
- Hit@10: `0.9500`
- Recall@5: `0.7658`
- Recall@10: `0.8425`
- nDCG@10: `0.6830`
- MRR: `0.7137`

Ambiguous MRR:

- Dense: `0.4183`
- Weighted RRF: `0.4592`
- Multi-Query: `0.5319`

Multi-Query improves coverage and ambiguous-query handling but does not exceed Weighted RRF in overall MRR.

### 8.5 Cross-Encoder Reranking

The original `MiniLM-L12-v2` reranker reduced overall quality:

- Weighted RRF MRR: `0.7247`
- MiniLM-L12 reranked MRR: `0.6461`

The broader five-model benchmark changed the interpretation.

Four tested rerankers failed to improve the Weighted RRF baseline, but `mixedbread-ai/mxbai-rerank-base-v2` improved it.

The strongest quality configuration is:

```text
Weighted RRF
  -> top 20 candidates
  -> mixedbread-ai/mxbai-rerank-base-v2
  -> final top 10
```

It achieved:

- Hit@1: `0.6700`
- Hit@10: `0.9700`
- Recall@10: `0.8758`
- nDCG@10: `0.7276`
- MRR: `0.7564`

The correct conclusion is:

> Cross-Encoder reranking is highly model-dependent. Mixedbread v2 improves retrieval quality, while the other evaluated rerankers do not improve the overall Weighted RRF baseline.

---

## 9. Historical 11-Case Pilot

Before the 100-case canonical benchmark existed, Cross-Encoder reranking was screened using a small 11-case development benchmark.

That pilot used:

- 11 evaluation cases
- one expected document per query
- binary relevance behavior
- reranker candidate multiplier: `2`
- up to 20 reranking candidates

Historical results:

| Strategy / Model | Hit@1 | Hit@3 | Hit@5 | Hit@10 | MRR |
| --- | ---: | ---: | ---: | ---: | ---: |
| Weighted RRF | **0.5455** | **0.9091** | **1.0000** | **1.0000** | **0.7303** |
| MiniLM-L6-v2 | 0.4545 | 0.9091 | 1.0000 | 1.0000 | 0.6591 |
| MiniLM-L12-v2 | **0.5455** | **0.9091** | 1.0000 | 1.0000 | 0.7197 |
| mxbai-rerank-base-v1 | 0.4545 | 0.9091 | 0.9091 | 0.9091 | 0.6667 |
| mxbai-rerank-base-v2 — later reproduction | **0.5455** | 0.8182 | **1.0000** | **1.0000** | 0.7227 |

Mixedbread v2 would have been the strongest reranker in the pilot, but it still would not have exceeded the Weighted RRF baseline.

The 100-case canonical benchmark later changed that conclusion.

The pilot should therefore be interpreted as a **development screening benchmark**, while the canonical 100-case benchmark is the source of truth for current retrieval-quality conclusions.

---

## 10. Quality Conclusions

The canonical benchmark supports the following conclusions:

1. **Weighted RRF is the strongest non-reranked global baseline.**
   - MRR: `0.7247`
   - Recall@10: `0.8392`
   - nDCG@10: `0.6788`

2. **Multi-Query improves coverage but does not improve overall MRR over Weighted RRF.**
   - MRR: `0.7137`
   - Recall@10: `0.8425`

3. **Cross-Encoder reranking is strongly model-dependent.**
   - MiniLM-L6, MiniLM-L12, BGE-reranker-v2-m3, and Mixedbread v1 did not improve the overall Weighted RRF baseline.
   - Mixedbread v2 did improve the baseline.

4. **The strongest offline retrieval-quality configuration is Mixedbread v2 with a 20-candidate pool.**
   - Hit@1: `0.6700`
   - Hit@10: `0.9700`
   - Recall@10: `0.8758`
   - nDCG@10: `0.7276`
   - MRR: `0.7564`

5. **More candidates do not automatically improve reranker quality.**
   - The 20-candidate Mixedbread v2 configuration outperformed the 40-candidate configuration on the major overall quality metrics.

6. **Different query categories favor different retrieval strategies.**
   - Ambiguous: Mixedbread v2
   - Cross-tool: BM25
   - Lexical: Mixedbread v2
   - Semantic: Mixedbread v2
   - Version-specific: Dense

---

## 11. Operational Evaluation Reference

This report intentionally stops at retrieval quality.

Operational performance and the final production deployment decision are evaluated separately in:

`benchmarks/retrieval/reports/retrieval_latency_v1.md`

The separation is intentional:

```text
retrieval_benchmark_v1.md
    -> How well does each strategy rank relevant evidence?

retrieval_latency_v1.md
    -> What operational cost is required to obtain that quality?
```

---

## 12. Benchmark Interpretation

The main retrieval-quality lessons are:

- Dense Retrieval provides a strong semantic baseline.
- BM25 contributes complementary lexical signals.
- Weighted RRF provides a strong fused baseline.
- Multi-Query improves evidence coverage.
- Cross-Encoder reranking is highly model-dependent.
- Mixedbread v2 is the only tested reranker that improves the overall Weighted RRF baseline.
- A 20-candidate Mixedbread v2 pool outperforms the 40-candidate pool on this benchmark.
- Different query categories favor different retrieval strategies.
- Additional retrieval stages and larger candidate pools should be validated empirically rather than assumed to improve ranking quality.

The central evaluation principle is:

> Retrieval architecture should be selected using measured evidence rather than model reputation or pipeline complexity.
