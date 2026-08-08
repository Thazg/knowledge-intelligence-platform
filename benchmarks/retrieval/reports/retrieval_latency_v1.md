# Retrieval Latency Benchmark v1

## Overview

This benchmark measures steady-state retrieval latency across the same 100 evaluation queries used in Retrieval Benchmark v1.

The benchmark excludes retriever and model initialization time.

Each retrieval strategy is warmed up before measurement.

Configuration:

- Queries: 100
- Warmup runs: 3
- Top K: 10
- Execution mode: sequential, single-process
- Metric unit: milliseconds

Multi-Query Retrieval uses frozen query rewrites during this benchmark. Therefore, its measured latency does not include live LLM query-rewriting latency.

## Latency Results

| Strategy | Mean | Median | P50 | P95 | P99 | Min | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Dense | 32.57 ms | 29.09 ms | 29.09 ms | 58.23 ms | 62.17 ms | 20.20 ms | 67.12 ms |
| BM25 | 119.37 ms | 121.28 ms | 121.28 ms | 159.07 ms | 171.92 ms | 49.53 ms | 177.75 ms |
| Weighted RRF | 161.50 ms | 163.89 ms | 163.89 ms | 212.62 ms | 224.67 ms | 67.59 ms | 241.98 ms |
| Multi-Query | 587.09 ms | 579.95 ms | 579.95 ms | 714.11 ms | 896.64 ms | 425.83 ms | 920.53 ms |
| Reranked Hybrid | 663.09 ms | 658.01 ms | 658.01 ms | 761.09 ms | 893.54 ms | 529.12 ms | 1018.85 ms |

## Relative Latency

Using Weighted RRF as the production baseline:

| Strategy | Mean Latency | Relative to Weighted RRF |
| --- | ---: | ---: |
| Dense | 32.57 ms | 0.20x |
| BM25 | 119.37 ms | 0.74x |
| Weighted RRF | 161.50 ms | 1.00x |
| Multi-Query | 587.09 ms | 3.64x |
| Reranked Hybrid | 663.09 ms | 4.11x |

## Quality vs Latency

| Strategy | MRR | Recall@5 | nDCG@5 | Mean Latency |
| --- | ---: | ---: | ---: | ---: |
| Dense | 0.6644 | 0.7025 | 0.6000 | 32.57 ms |
| BM25 | 0.6083 | 0.6250 | 0.5257 | 119.37 ms |
| Weighted RRF | **0.7247** | 0.7308 | 0.6402 | 161.50 ms |
| Multi-Query | 0.7137 | **0.7658** | **0.6565** | 587.09 ms |
| Reranked Hybrid | 0.6461 | 0.6642 | 0.5851 | 663.09 ms |

## Findings

Dense Retrieval provides the lowest latency by a large margin, with a mean latency of 32.57 ms.

However, Dense Retrieval also produces lower overall retrieval quality than Weighted RRF.

Weighted RRF increases mean latency to 161.50 ms but achieves the highest overall MRR of 0.7247.

This represents a strong quality-versus-latency trade-off for the default retrieval path.

Multi-Query Retrieval increases mean latency to 587.09 ms, approximately 3.64 times the latency of Weighted RRF.

Although Multi-Query improves retrieval coverage, including Recall@5 and nDCG@5, it does not improve overall MRR.

Additionally, this benchmark uses frozen query rewrites and therefore does not include live LLM query-rewriting latency.

Production latency for live Multi-Query Retrieval would therefore be expected to be higher than the measurements reported here.

Reranked Hybrid Retrieval has the highest mean latency at 663.09 ms, approximately 4.11 times the latency of Weighted RRF.

The reranker also produces lower overall retrieval quality than Weighted RRF.

This makes global Cross-Encoder reranking unattractive under the current configuration because it increases computational cost while reducing retrieval quality.

## Production Decision

Weighted RRF remains the recommended production retrieval strategy.

It provides:

- The highest overall MRR.
- Strong retrieval coverage.
- Strong semantic and lexical performance.
- Significantly lower latency than Multi-Query Retrieval and Cross-Encoder reranking.
- Lower operational complexity than advanced retrieval paths.

The recommended default architecture remains:

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

Multi-Query Retrieval should remain an optional advanced strategy for ambiguous or difficult queries where additional retrieval coverage may justify increased latency.

Cross-Encoder reranking should remain experimental and should not be enabled globally under the current configuration.

## Limitations

This benchmark measures steady-state retrieval latency only.

It does not measure:

- Concurrent request throughput.
- Load-test performance.
- Cold-start latency.
- Model initialization time.
- Live LLM query-rewrite latency.
- End-to-end RAG generation latency.
- GPU or CPU utilization.
- Memory consumption.

These factors should be evaluated separately in later production-performance benchmarks.