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
- Reranker model: `cross-encoder/ms-marco-MiniLM-L12-v2`
- Candidate multiplier: 4
- Candidate pool at top_k=10: up to 40 candidates
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
| Reranked Hybrid (MiniLM-L12-v2) | 0.5300 | 0.7200 | 0.8000 | 0.9200 | 0.5792 | 0.6642 | 0.7858 | 0.5489 | 0.5851 | 0.6266 | 0.6461 |

## Category MRR

| Category | Dense | BM25 | Weighted RRF | Multi-Query | Reranked Hybrid (MiniLM-L12-v2) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ambiguous | 0.4183 | 0.2681 | 0.4592 | **0.5319** | 0.5005 |
| Cross-tool | 0.5671 | **0.6308** | 0.6181 | 0.5972 | 0.5226 |
| Lexical | 0.7363 | 0.6660 | **0.8792** | 0.8517 | 0.7747 |
| Semantic | 0.7083 | 0.7000 | **0.8088** | 0.8000 | 0.6153 |
| Version-specific | **0.8917** | 0.7767 | 0.8583 | 0.7875 | 0.8175 |

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
- Reranked Hybrid: 0.6461

Hit@1 also decreased:

- Weighted RRF: 0.6200
- Reranked Hybrid: 0.5300

Overall ranking-quality metrics also declined:

- Weighted RRF nDCG@3: 0.6010
- Reranked Hybrid nDCG@3: 0.5489

- Weighted RRF nDCG@10: 0.6788
- Reranked Hybrid nDCG@10: 0.6266

Reranking also reduced retrieval quality across most query categories.

Ambiguous-query MRR:

- Weighted RRF: 0.4592
- Reranked Hybrid: 0.5005

Although reranking improved ambiguous-query MRR relative to Weighted RRF, Multi-Query Retrieval remained stronger at 0.5319.

Cross-tool MRR decreased:

- Weighted RRF: 0.6181
- Reranked Hybrid: 0.5226

Lexical MRR decreased:

- Weighted RRF: 0.8792
- Reranked Hybrid: 0.7747

Semantic MRR decreased:

- Weighted RRF: 0.8088
- Reranked Hybrid: 0.6153

Version-specific MRR also decreased:

- Weighted RRF: 0.8583
- Reranked Hybrid: 0.8175

These results indicate that the selected Cross-Encoder reranker,
`cross-encoder/ms-marco-MiniLM-L12-v2`, does not provide sufficient
quality improvement to justify applying reranking globally.

The only category where the reranker improved over Weighted RRF was
ambiguous queries, but Multi-Query Retrieval still achieved higher MRR
for that category.

Weighted RRF therefore remains the preferred global retrieval strategy,
while reranking remains an experimental component rather than part of
the default production path.

## Category-Specific Behavior

The best-performing strategy differs by query category.

| Category | Best Strategy | MRR |
| --- | --- | ---: |
| Ambiguous | Multi-Query | 0.5319 |
| Cross-tool | BM25 | 0.6308 |
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

Cross-Encoder reranking remains an experimental component.

It improved ambiguous-query MRR relative to Weighted RRF, but Multi-Query Retrieval still performed better on ambiguous queries. It did not improve the strongest strategy in any benchmark category.

The current evidence therefore does not justify enabling Cross-Encoder reranking in the production retrieval path.

## Quality vs Latency

Retrieval quality must be considered together with operational cost.

The latency benchmark measures steady-state retrieval time across the same 100 evaluation queries used in Retrieval Benchmark v1.

| Strategy | MRR | Recall@5 | nDCG@5 | Mean Latency |
| --- | ---: | ---: | ---: | ---: |
| Dense | 0.6644 | 0.7025 | 0.6000 | 32.57 ms |
| BM25 | 0.6083 | 0.6250 | 0.5257 | 119.37 ms |
| Weighted RRF | **0.7247** | 0.7308 | 0.6402 | 161.50 ms |
| Multi-Query | 0.7137 | **0.7658** | **0.6565** | 587.09 ms |
| Reranked Hybrid | 0.6461 | 0.6642 | 0.5851 | 663.09 ms |

Weighted RRF provides the strongest overall quality-versus-latency trade-off.

Compared with Dense Retrieval, Weighted RRF increases mean latency from 32.57 ms to 161.50 ms while improving MRR from 0.6644 to 0.7247.

Multi-Query Retrieval increases mean latency to 587.09 ms, approximately 3.64 times the latency of Weighted RRF.

Although Multi-Query improves Recall@5 and nDCG@5, it does not improve overall MRR.

The reported Multi-Query latency uses frozen query rewrites and therefore does not include live LLM query-rewriting latency.

Reranked Hybrid Retrieval increases mean latency to 663.09 ms, approximately 4.11 times the latency of Weighted RRF, while also reducing overall retrieval quality.

These results reinforce Weighted RRF as the production default.

Advanced retrieval stages should only be activated when their expected quality benefit justifies the additional latency and computational cost.

## Future Adaptive Retrieval

The benchmark provides evidence that different query categories can benefit from different retrieval strategies.

A future adaptive retrieval architecture could therefore be explored:

```text
                         Query
                           |
                           v
                    Query Classifier
                           |
             +-------------+-------------+
             |                           |
             v                           v
      Standard Queries             Difficult /
             |                  Ambiguous Queries
             v                           |
        Weighted RRF                     v
                                  Multi-Query
```

Cross-Encoder reranking remains an experimental component and is not currently included in the proposed adaptive production path.

Category-specific routing should not be implemented directly from the current benchmark results.

The adaptive strategy should only be adopted after additional validation to avoid overfitting routing decisions to the current benchmark.

A separate development or tuning benchmark should be introduced before tuning routing rules, query classification, or retrieval strategy selection.

## Benchmark Interpretation

The benchmark demonstrates several important retrieval-system behaviors:

- Dense Retrieval provides a strong semantic baseline.
- BM25 contributes complementary lexical signals.
- Weighted RRF provides the strongest overall first-stage retrieval quality.
- Multi-Query Retrieval improves evidence coverage and ambiguous-query handling.
- Cross-Encoder reranking did not improve overall retrieval quality and did not outperform the best strategy in any benchmark category.
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
