# Retrieval Benchmark v1

## Overview

This benchmark evaluates retrieval quality across 100 manually verified evaluation cases.

The benchmark contains five categories:

- Semantic: 20 cases
- Lexical: 20 cases
- Ambiguous: 20 cases
- Version-specific: 20 cases
- Cross-tool: 20 cases

Total: 100 cases

Each case may contain multiple relevant documents with graded relevance:

- 3 = highly relevant
- 2 = relevant
- 1 = partially relevant

## Retrieval Strategies

The following retrieval strategies were evaluated:

1. Dense Retrieval
2. BM25
3. Weighted Reciprocal Rank Fusion
4. Multi-Query Retrieval
5. Weighted RRF + Cross-Encoder Reranking

### Dense Retrieval

Dense retrieval uses:

- Embedding model: `BAAI/bge-small-en-v1.5`
- Vector database: Qdrant

### Weighted RRF

Weighted Reciprocal Rank Fusion combines Dense and BM25 retrieval.

Configuration:

- Dense weight: 0.7
- BM25 weight: 0.3
- RRF k: 60

### Multi-Query Retrieval

Multi-Query Retrieval expands the original query into multiple rewritten queries.

Frozen query rewrites are used during evaluation to ensure deterministic and reproducible benchmark results.

### Cross-Encoder Reranking

Cross-Encoder reranking is applied on top of Weighted RRF candidates.

Configuration:

- Base retriever: Weighted RRF
- Reranker model: `mixedbread-ai/mxbai-rerank-base-v1`
- Candidate multiplier: 4
- Batch size: 16

## Evaluation Metrics

The benchmark evaluates retrieval using:

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

Hit@K measures whether at least one relevant document appears within the top K results.

Recall@K measures how much of the relevant document set is retrieved within the top K results.

nDCG@K evaluates ranking quality while accounting for graded relevance and result position.

MRR measures how early the first relevant document appears in the ranking.

## Overall Results

| Retriever | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Recall@3 | Recall@5 | Recall@10 | nDCG@3 | nDCG@5 | nDCG@10 | MRR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Dense | 0.5300 | 0.7700 | 0.8200 | 0.8900 | 0.6225 | 0.7025 | 0.7958 | 0.5697 | 0.6000 | 0.6364 | 0.6644 |
| BM25 | 0.4700 | 0.7100 | 0.8000 | 0.8700 | 0.5317 | 0.6250 | 0.7308 | 0.4844 | 0.5257 | 0.5650 | 0.6083 |
| Weighted RRF | **0.6200** | **0.8100** | 0.8700 | 0.9300 | **0.6408** | 0.7308 | 0.8392 | **0.6010** | 0.6402 | 0.6788 | **0.7247** |
| Multi-Query | 0.5800 | **0.8100** | **0.8800** | **0.9500** | 0.6358 | **0.7658** | **0.8425** | 0.6007 | **0.6565** | **0.6830** | 0.7137 |
| Reranked Hybrid | 0.5300 | 0.7900 | **0.8800** | 0.9200 | 0.6192 | 0.7492 | 0.8208 | 0.5856 | 0.6375 | 0.6628 | 0.6762 |

## Category MRR

| Category | Dense | BM25 | Weighted RRF | Multi-Query | Reranked Hybrid |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ambiguous | 0.4183 | 0.2681 | 0.4592 | 0.5319 | **0.5889** |
| Cross-tool | 0.5671 | 0.6308 | 0.6181 | 0.5972 | **0.6433** |
| Lexical | 0.7363 | 0.6660 | **0.8792** | 0.8517 | 0.6937 |
| Semantic | 0.7083 | 0.7000 | **0.8088** | 0.8000 | 0.6683 |
| Version-specific | **0.8917** | 0.7767 | 0.8583 | 0.7875 | 0.7867 |

## Findings

### Dense Retrieval

Dense Retrieval provides a strong general-purpose semantic baseline.

It performed particularly well on version-specific queries:

- Version-specific MRR: 0.8917
- Version-specific Hit@1: 0.8500
- Version-specific Recall@3: 0.9250
- Version-specific nDCG@3: 0.8578

Dense Retrieval was considerably weaker on ambiguous queries:

- Ambiguous MRR: 0.4183
- Ambiguous Hit@1: 0.3000
- Ambiguous Recall@10: 0.5250
- Ambiguous nDCG@10: 0.3672

This suggests that dense semantic similarity alone is not sufficient for queries with underspecified intent.

### BM25

BM25 achieved lower overall performance than Dense Retrieval:

- Dense MRR: 0.6644
- BM25 MRR: 0.6083

However, BM25 contributed useful lexical signals, particularly for cross-tool retrieval.

Cross-tool results:

- BM25 MRR: 0.6308
- Dense MRR: 0.5671

BM25 therefore remains valuable as a complementary first-stage retriever even though it is not the strongest standalone strategy.

### Weighted RRF

Weighted RRF achieved the strongest overall ranking performance.

Compared with Dense Retrieval:

- Hit@1 improved from 0.5300 to 0.6200.
- MRR improved from 0.6644 to 0.7247.
- Recall@10 improved from 0.7958 to 0.8392.
- nDCG@10 improved from 0.6364 to 0.6788.

Weighted RRF performed especially well on lexical and semantic queries.

Lexical:

- Dense MRR: 0.7363
- BM25 MRR: 0.6660
- Weighted RRF MRR: 0.8792

Semantic:

- Dense MRR: 0.7083
- BM25 MRR: 0.7000
- Weighted RRF MRR: 0.8088

These results show that Dense and BM25 retrieval provide complementary ranking signals that become more useful when combined.

### Multi-Query Retrieval

Multi-Query Retrieval achieved the strongest overall retrieval coverage.

Results:

- Hit@5: 0.8800
- Hit@10: 0.9500
- Recall@5: 0.7658
- Recall@10: 0.8425
- nDCG@5: 0.6565
- nDCG@10: 0.6830

Multi-Query Retrieval was especially effective for ambiguous queries.

Ambiguous MRR:

- Dense: 0.4183
- Weighted RRF: 0.4592
- Multi-Query: 0.5319

This suggests that rewriting an underspecified query into several alternative formulations can improve retrieval coverage and intent matching.

However, Multi-Query Retrieval did not achieve the highest overall MRR:

- Weighted RRF MRR: 0.7247
- Multi-Query MRR: 0.7137

Multi-Query therefore improves coverage but introduces additional query rewriting and retrieval cost.

### Cross-Encoder Reranking

Cross-Encoder reranking did not improve overall retrieval quality when applied globally.

Overall MRR decreased:

- Weighted RRF: 0.7247
- Reranked Hybrid: 0.6762

Hit@1 also decreased:

- Weighted RRF: 0.6200
- Reranked Hybrid: 0.5300

Overall ranking-quality metrics also declined:

- Weighted RRF nDCG@3: 0.6010
- Reranked Hybrid nDCG@3: 0.5856

- Weighted RRF nDCG@10: 0.6788
- Reranked Hybrid nDCG@10: 0.6628

However, reranking produced strong gains in difficult categories.

Ambiguous-query MRR improved:

- Weighted RRF: 0.4592
- Reranked Hybrid: 0.5889

Cross-tool MRR improved:

- Weighted RRF: 0.6181
- Reranked Hybrid: 0.6433

At the same time, reranking significantly reduced performance for lexical and semantic queries.

Lexical MRR:

- Weighted RRF: 0.8792
- Reranked Hybrid: 0.6937

Semantic MRR:

- Weighted RRF: 0.8088
- Reranked Hybrid: 0.6683

Version-specific MRR also decreased:

- Weighted RRF: 0.8583
- Reranked Hybrid: 0.7867

These results indicate that the current Cross-Encoder configuration should not be applied globally.

## Category-Specific Behavior

The best-performing strategy differs by query category.

| Category | Best Strategy | MRR |
| --- | --- | ---: |
| Ambiguous | Reranked Hybrid | 0.5889 |
| Cross-tool | Reranked Hybrid | 0.6433 |
| Lexical | Weighted RRF | 0.8792 |
| Semantic | Weighted RRF | 0.8088 |
| Version-specific | Dense | 0.8917 |

This demonstrates that a single retrieval strategy is not optimal for every query type.

The benchmark also shows that adding more retrieval stages does not automatically improve overall quality.

## Production Decision

Weighted RRF is selected as the default retrieval strategy.

Rationale:

- Highest overall MRR.
- Highest Hit@1.
- Strong performance across semantic and lexical categories.
- Better overall ranking quality than standalone Dense and BM25 retrieval.
- Lower operational complexity than Multi-Query Retrieval.
- More reliable globally than the current Cross-Encoder reranking configuration.

The production default is therefore:

```text
Query
  |
  v
Dense Retrieval
  +
BM25 Retrieval
  |
  v
Weighted RRF
  |
  v
Final Retrieved Context
```

Multi-Query Retrieval should remain available as an advanced strategy for ambiguous or difficult queries.

Cross-Encoder reranking should not currently be enabled for all queries.

Its strong performance on ambiguous and cross-tool cases suggests that it may be useful as a selectively activated retrieval stage.

## Future Adaptive Retrieval

The benchmark provides evidence for a future adaptive retrieval architecture.

A possible routing strategy is:

```text
                         Query
                           |
                           v
                    Query Classifier
                           |
             +-------------+-------------+
             |                           |
             v                           v
   Normal / lexical /             Ambiguous /
 semantic / version-specific       cross-tool
             |                           |
             v                           v
        Weighted RRF               Advanced Path
                                         |
                              +----------+----------+
                              |                     |
                              v                     v
                         Multi-Query          Cross-Encoder
                              |                  Reranking
                              +----------+----------+
                                         |
                                         v
                                  Final Retrieval
```

This architecture is not yet selected as the production default.

The adaptive strategy should only be adopted after additional validation to avoid overfitting routing decisions to the current benchmark.

A separate development or tuning benchmark should be introduced before tuning routing rules or reranker configuration.

## Benchmark Interpretation

The benchmark demonstrates several important retrieval-system behaviors:

- Dense Retrieval provides a strong semantic baseline.
- BM25 contributes complementary lexical signals.
- Weighted RRF provides the strongest overall first-stage retrieval quality.
- Multi-Query Retrieval improves evidence coverage and ambiguous-query handling.
- Cross-Encoder reranking improves difficult categories but currently harms overall ranking quality.
- Different query categories benefit from different retrieval strategies.
- Additional retrieval stages should be validated empirically rather than assumed to improve quality.

These results support a layered retrieval architecture rather than assuming that a single retrieval method or a deeper pipeline is always better.

## Current Retrieval Architecture

Based on Retrieval Benchmark v1, the current recommended architecture is:

```text
                         Query
                           |
                           v
                   Weighted RRF
                 /              \
                /                \
        Dense Retrieval       BM25 Retrieval
                \                /
                 \              /
                  +------------+
                         |
                         v
                Ranked Documents
                         |
                         v
                    RAG Context
```

Weighted RRF remains the production default until latency and end-to-end generation evaluation provide evidence for a different architecture.

## Next Evaluation Stage

The next evaluation stage should focus on operational performance.

The following retrieval strategies should be benchmarked:

- Dense Retrieval
- BM25
- Weighted RRF
- Multi-Query Retrieval
- Cross-Encoder Reranking

Latency measurements should include:

- Mean latency
- Median latency
- p50 latency
- p95 latency
- p99 latency
- Minimum latency
- Maximum latency

The benchmark should also compare:

- Retrieval quality
- Retrieval latency
- Additional model inference cost
- Query rewriting overhead
- Cross-Encoder reranking overhead

The final production architecture should be selected using both retrieval quality and operational cost.

The key objective of the next stage is to answer:

> How much additional latency and computational cost is required for each retrieval-quality improvement?

This will enable a quality-versus-latency comparison across all evaluated retrieval strategies.