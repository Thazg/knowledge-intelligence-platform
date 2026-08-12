# Retrieval Latency Benchmark v1

## 1. Overview

This benchmark measures steady-state retrieval latency across the same 100 canonical evaluation queries used in Retrieval Benchmark v1.

This report is the operational companion to `retrieval_benchmark_v1.md`.

The quality report answers:

> How well does each strategy rank relevant evidence?

This latency report answers:

> What operational cost is required to obtain that quality?

The benchmark excludes retriever and model initialization time.

Configuration:

- Queries: 100
- Warmup runs: 3
- Top K: 10
- Execution mode: sequential, single-process
- Metric unit: milliseconds

Multi-Query Retrieval uses frozen query rewrites. Its measured latency therefore does not include live LLM query-rewriting latency.

The current reranking configuration is:

- Model: `mixedbread-ai/mxbai-rerank-base-v2`
- Reranker candidate multiplier: `2`
- Candidate pool at `top_k=10`: up to `20`

Historical reranker measurements are retained later in this report for comparison.

---

## 2. Current Latency Results

| Strategy | Candidate Pool | Mean | P95 |
| --- | ---: | ---: | ---: |
| Dense | — | 27.32 ms | 46.20 ms |
| BM25 | — | 117.04 ms | 150.64 ms |
| Weighted RRF | — | 162.28 ms | 216.82 ms |
| Multi-Query | — | 619.56 ms | 849.02 ms |
| Reranked Hybrid — Mixedbread v2 | 20 | 4076.07 ms | 4676.60 ms |

The exact machine-readable measurements, including median, P50, P99, minimum, and maximum values, are stored in:

```text
benchmarks/retrieval/reports/retrieval_latency_v1.json
```

---

## 3. Relative Latency

Using Weighted RRF as the production baseline:

| Strategy | Candidate Pool | Mean Latency | Relative to Weighted RRF |
| --- | ---: | ---: | ---: |
| Dense | — | 27.32 ms | 0.17x |
| BM25 | — | 117.04 ms | 0.72x |
| Weighted RRF | — | 162.28 ms | 1.00x |
| Multi-Query | — | 619.56 ms | 3.82x |
| Reranked Hybrid — Mixedbread v2 | 20 | 4076.07 ms | 25.12x |

---

## 4. Quality vs Latency

The quality values below come from Retrieval Benchmark v1.

| Strategy | Candidate Pool | MRR | Recall@10 | nDCG@10 | Mean Latency | P95 Latency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Dense | — | 0.6644 | 0.7958 | 0.6364 | 27.32 ms | 46.20 ms |
| BM25 | — | 0.6083 | 0.7308 | 0.5650 | 117.04 ms | 150.64 ms |
| Weighted RRF | — | 0.7247 | 0.8392 | 0.6788 | **162.28 ms** | **216.82 ms** |
| Multi-Query | — | 0.7137 | 0.8425 | 0.6830 | 619.56 ms | 849.02 ms |
| **Reranked Hybrid — Mixedbread v2** | **20** | **0.7564** | **0.8758** | **0.7276** | **4076.07 ms** | **4676.60 ms** |

---

## 5. Findings

### 5.1 Dense Retrieval

Dense Retrieval is the fastest evaluated strategy:

- Mean: `27.32 ms`
- P95: `46.20 ms`

Its overall retrieval quality is lower than Weighted RRF.

### 5.2 BM25

BM25 has:

- Mean: `117.04 ms`
- P95: `150.64 ms`

It is faster than Weighted RRF but has lower overall retrieval quality.

### 5.3 Weighted RRF

Weighted RRF has:

- Mean: `162.28 ms`
- P95: `216.82 ms`
- MRR: `0.7247`
- Recall@10: `0.8392`
- nDCG@10: `0.6788`

It provides the strongest overall quality-versus-latency balance for the default retrieval path.

### 5.4 Multi-Query Retrieval

Multi-Query has:

- Mean: `619.56 ms`
- P95: `849.02 ms`

This is approximately `3.82x` the mean latency of Weighted RRF.

It improves coverage but does not improve overall MRR over Weighted RRF.

Because frozen rewrites are used, live LLM rewrite-generation time is not included.

### 5.5 Mixedbread v2 Reranking — Pool 20

Mixedbread v2 with 20 candidates has:

- MRR: `0.7564`
- Recall@10: `0.8758`
- nDCG@10: `0.7276`
- Mean: `4076.07 ms`
- P95: `4676.60 ms`

Compared with Weighted RRF:

- MRR improves from `0.7247` to `0.7564`.
- Recall@10 improves from `0.8392` to `0.8758`.
- nDCG@10 improves from `0.6788` to `0.7276`.
- Mean retrieval latency increases from `162.28 ms` to `4076.07 ms`.
- Mean latency is approximately `25.12x` higher.
- P95 latency is approximately `21.57x` higher.

The reranked path therefore adds approximately `3.9 seconds` of mean retrieval work before generation begins.

---

## 6. Historical Reranker Comparisons

Earlier controlled experiments measured two additional reranking configurations.

### 6.1 MiniLM-L12 — Pool 40

Historical configuration:

- Model: `cross-encoder/ms-marco-MiniLM-L12-v2`
- Candidate multiplier: `4`
- Candidate pool: up to `40`

Historical result:

- Mean latency: `663.09 ms`
- P95 latency: `761.09 ms`
- MRR: `0.6461`
- Recall@10: `0.7858`
- nDCG@10: `0.6268`

This configuration was both slower and lower quality than Weighted RRF.

### 6.2 Mixedbread v2 — Pool 40

Historical configuration:

- Model: `mixedbread-ai/mxbai-rerank-base-v2`
- Candidate multiplier: `4`
- Candidate pool: up to `40`

Historical result:

- Mean latency: `7606.74 ms`
- P95 latency: `8402.73 ms`
- MRR: `0.7475`
- Recall@10: `0.8525`
- nDCG@10: `0.7156`

Reducing the candidate pool from 40 to 20 improved both quality and latency:

- MRR: `0.7475 -> 0.7564`
- Recall@10: `0.8525 -> 0.8758`
- nDCG@10: `0.7156 -> 0.7276`
- Mean latency: `7606.74 ms -> 4076.07 ms`
- P95 latency: `8402.73 ms -> 4676.60 ms`

This makes the 20-candidate Mixedbread v2 configuration the preferred reranking configuration among those evaluated.

Historical measurements are retained for experimental comparison and are not part of the current machine-readable latency run.

---

## 7. Production Decision

### 7.1 Quality-Best Configuration

The highest-quality retrieval configuration evaluated is:

```text
Query
  |
  v
Dense + BM25
  |
  v
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

Quality:

- Hit@1: `0.6700`
- Hit@10: `0.9700`
- Recall@10: `0.8758`
- nDCG@10: `0.7276`
- MRR: `0.7564`

### 7.2 Production Default

Despite the quality improvement, **Weighted RRF remains the production default**.

Rationale:

- Mean retrieval latency: approximately `162.28 ms`
- P95 retrieval latency: approximately `216.82 ms`
- MRR: `0.7247`
- Recall@10: `0.8392`
- nDCG@10: `0.6788`
- Lower operational complexity than advanced reranking paths

Mixedbread v2 improves retrieval quality, but its current mean retrieval latency is approximately `25.12x` higher than Weighted RRF.

The production default remains:

```text
Query
  |
  v
Dense Retrieval + BM25 Retrieval
  |
  v
Weighted RRF
  |
  v
Final Retrieved Context
```

Mixedbread v2 reranking is classified as:

```text
Quality-best experimental strategy
NOT enabled globally
Candidate for future selective/adaptive routing
```

The important distinction is:

> Mixedbread v2 is not rejected because of retrieval quality. It is not enabled globally because its current operational cost is too high relative to the measured quality gain.

Multi-Query likewise remains an optional advanced strategy.

---

## 8. Limitations

This benchmark measures steady-state retrieval latency only.

It does not measure:

- Concurrent request throughput
- Load-test behavior
- Cold-start latency
- Model initialization time
- Live LLM query-rewrite latency
- End-to-end RAG generation latency
- GPU acceleration
- Quantized reranker inference
- CPU or GPU utilization
- Memory consumption
- Batched multi-request throughput

The Mixedbread v2 latency values reflect the current local runtime and hardware configuration and should not be interpreted as universal model latency.

Potential future optimization areas include:

- GPU inference
- Quantization
- Selective reranking
- Query routing
- Batched inference
- Deployment-specific model optimization

---

## 9. Final Interpretation

Weighted RRF remains the strongest production default because it combines strong retrieval quality with sub-second retrieval latency.

Mixedbread v2 with a 20-candidate pool produces the best measured retrieval quality, but its current inference cost is too high for global use.

The current evidence supports:

```text
Weighted RRF
    -> default production retriever

Mixedbread v2, candidate multiplier = 2
    -> best quality-oriented experimental retriever

Multi-Query
    -> optional coverage-oriented strategy
```

Future retrieval work should focus on selective or adaptive activation rather than applying expensive retrieval stages to every query.
