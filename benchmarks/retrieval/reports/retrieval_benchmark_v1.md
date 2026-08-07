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

Dense retrieval uses:

- Embedding model: `BAAI/bge-small-en-v1.5`
- Vector database: Qdrant

Weighted RRF uses:

- Dense weight: 0.7
- BM25 weight: 0.3
- RRF k: 60

Multi-Query Retrieval uses frozen query rewrites to ensure deterministic and reproducible evaluation.

## Overall Results

| Retriever | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Recall@3 | Recall@5 | Recall@10 | nDCG@3 | nDCG@5 | nDCG@10 | MRR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Dense | 0.5300 | 0.7700 | 0.8200 | 0.8900 | 0.6225 | 0.7025 | 0.7958 | 0.5697 | 0.6000 | 0.6364 | 0.6644 |
| BM25 | 0.4700 | 0.7100 | 0.8000 | 0.8700 | 0.5317 | 0.6250 | 0.7308 | 0.4844 | 0.5257 | 0.5650 | 0.6083 |
| Weighted RRF | **0.6200** | **0.8100** | 0.8700 | 0.9300 | **0.6408** | 0.7308 | 0.8392 | **0.6010** | 0.6402 | 0.6788 | **0.7247** |
| Multi-Query | 0.5800 | **0.8100** | **0.8800** | **0.9500** | 0.6358 | **0.7658** | **0.8425** | 0.6007 | **0.6565** | **0.6830** | 0.7137 |

## Category MRR

| Category | Dense | BM25 | Weighted RRF | Multi-Query |
|---|---:|---:|---:|---:|
| Ambiguous | 0.4183 | 0.2681 | 0.4592 | **0.5319** |
| Cross-tool | 0.5671 | **0.6308** | 0.6181 | 0.5972 |
| Lexical | 0.7363 | 0.6660 | **0.8792** | 0.8517 |
| Semantic | 0.7083 | 0.7000 | **0.8088** | 0.8000 |
| Version-specific | **0.8917** | 0.7767 | 0.8583 | 0.7875 |

## Findings

Weighted RRF achieved the strongest overall ranking performance.

Compared with Dense Retrieval:

- Hit@1 improved from 0.5300 to 0.6200.
- MRR improved from 0.6644 to 0.7247.
- Recall@10 improved from 0.7958 to 0.8392.
- nDCG@10 improved from 0.6364 to 0.6788.

Multi-Query Retrieval achieved the highest retrieval coverage:

- Hit@5: 0.8800
- Hit@10: 0.9500
- Recall@5: 0.7658
- Recall@10: 0.8425
- nDCG@5: 0.6565
- nDCG@10: 0.6830

Multi-Query Retrieval was particularly effective for ambiguous queries, where it achieved an MRR of 0.5319 compared with 0.4592 for Weighted RRF.

BM25 performed especially well on cross-tool queries and achieved the highest cross-tool MRR of 0.6308.

Dense Retrieval achieved the strongest performance on version-specific queries with an MRR of 0.8917.

## Production Decision

Weighted RRF is selected as the default retrieval strategy.

Rationale:

- Highest overall MRR.
- Highest Hit@1.
- Strong performance across semantic and lexical categories.
- Better quality than standalone Dense and BM25 retrieval.
- Lower retrieval complexity than Multi-Query Retrieval.

Multi-Query Retrieval should remain available as an advanced retrieval strategy for ambiguous or difficult queries.

A future adaptive retrieval layer may route queries dynamically:

```text
Normal query
    |
    v
Weighted RRF

Ambiguous / difficult query
    |
    v
Multi-Query Retrieval
    |
    v
Weighted RRF