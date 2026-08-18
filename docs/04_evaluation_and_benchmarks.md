# Evaluation and Benchmarks

## 1. Purpose

Enterprise KIP treats evaluation as a first-class engineering activity.

The v1 system was not selected by assuming that a more complex retrieval or generation pipeline would be better. Each major architecture decision was evaluated using frozen benchmark artifacts, measured quality, latency, and operational behavior.

The evaluation stack covers:

```text
retrieval quality
→ retrieval latency
→ generation behavior
→ end-to-end RAG behavior
→ adaptive retrieval decisions
→ load and performance behavior
→ cloud deployment characterization
```

This document summarizes the benchmark hierarchy and the production decisions that followed from it.

---

## 2. Benchmark Hierarchy

Canonical benchmark artifacts live under:

```text
benchmarks/
├── retrieval/
├── generation/
├── e2e/
└── load/
```

The main reports are:

```text
benchmarks/retrieval/reports/retrieval_benchmark_v1.md
benchmarks/retrieval/reports/retrieval_latency_v1.md
benchmarks/retrieval/routing/adaptive_retrieval_v1_decision.md
benchmarks/generation/reports/generation_benchmark_v1.md
benchmarks/e2e/reports/e2e_v1_decision.md
```

Raw review material, temporary benchmark outputs, exploratory probes, and local `.benchmark-results/` artifacts are not treated as canonical release documentation unless they are deliberately promoted.

---

## 3. Retrieval Benchmark v1

### Dataset

The canonical retrieval benchmark contains 100 manually verified cases:

| Category | Cases |
|---|---:|
| Semantic | 20 |
| Lexical | 20 |
| Ambiguous | 20 |
| Version-specific | 20 |
| Cross-tool | 20 |
| **Total** | **100** |

The benchmark uses graded relevance:

```text
3 = highly relevant
2 = relevant
1 = partially relevant
```

### Strategies Evaluated

The benchmark compares:

1. Dense Retrieval
2. BM25
3. Weighted Reciprocal Rank Fusion
4. Multi-Query Retrieval
5. Weighted RRF + Cross-Encoder reranking

### Canonical Quality Results

| Retriever | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Recall@10 | nDCG@10 | MRR |
|---|---:|---:|---:|---:|---:|---:|---:|
| Dense | 0.5300 | 0.7700 | 0.8200 | 0.8900 | 0.7958 | 0.6364 | 0.6644 |
| BM25 | 0.4700 | 0.7100 | 0.8000 | 0.8700 | 0.7308 | 0.5650 | 0.6083 |
| **Weighted RRF** | **0.6200** | **0.8100** | 0.8700 | 0.9300 | 0.8392 | 0.6788 | 0.7247 |
| Multi-Query | 0.5800 | **0.8100** | **0.8800** | 0.9500 | 0.8425 | 0.6830 | 0.7137 |
| Mixedbread v2 reranked, pool 20 | **0.6700** | **0.8100** | 0.8700 | **0.9700** | **0.8758** | **0.7276** | **0.7564** |

### Main Retrieval Conclusion

Mixedbread v2 reranking produced the strongest offline retrieval quality.

However, Weighted RRF remained the production default because it provided the best overall quality-versus-latency trade-off for the deterministic v1 path.

The production retrieval configuration is:

```text
Dense weight       0.7
BM25 weight        0.3
RRF k              60
Top-k              10
```

---

## 4. Retrieval Latency Benchmark v1

Steady-state retrieval latency was measured over the same 100 canonical queries.

The benchmark excludes retriever and model initialization time.

| Strategy | Candidate Pool | Mean | P95 |
|---|---:|---:|---:|
| Dense | — | 27.32 ms | 46.20 ms |
| BM25 | — | 117.04 ms | 150.64 ms |
| **Weighted RRF** | — | **162.28 ms** | **216.82 ms** |
| Multi-Query | — | 619.56 ms | 849.02 ms |
| Mixedbread v2 reranked | 20 | 4076.07 ms | 4676.60 ms |

Relative to Weighted RRF:

```text
Dense                  0.17x
BM25                   0.72x
Weighted RRF           1.00x
Multi-Query            3.82x
Mixedbread reranking  25.12x
```

The reranked path improved quality but added roughly four seconds of retrieval work before generation.

This was not justified as the global default.

---

## 5. Adaptive Retrieval v1

Adaptive Retrieval v1 tested whether expensive retrieval should be activated only when it materially improved a query.

Three routes were evaluated:

```text
STANDARD
Weighted RRF

COVERAGE
Multi-Query retrieval

HIGH_QUALITY
Weighted RRF + Mixedbread v2 reranking
```

On the 45-query routing development benchmark:

| Metric | STANDARD | COVERAGE | HIGH_QUALITY |
|---|---:|---:|---:|
| Hit@10 | 1.0000 | 1.0000 | 1.0000 |
| Recall@10 | **0.7635** | 0.7152 | 0.7191 |
| nDCG@10 | 0.7063 | 0.6981 | **0.7292** |
| MRR | 0.9481 | **0.9611** | 0.9600 |
| Mean latency | **206.19 ms** | 650.94 ms | 3874.78 ms |
| P95 latency | **281.23 ms** | 881.10 ms | 4352.34 ms |

The best tested routing rule achieved only:

```text
Precision        0.667
Recall           0.667
Activation rate  0.209
```

HIGH_QUALITY retrieval was roughly 19x slower than STANDARD.

### Production Decision

Automatic adaptive retrieval is **not shipped in v1**.

The deterministic production policy remains:

```text
Uncertain
   ↓
STANDARD
   ↓
Weighted RRF
```

Multi-Query and reranking remain experimental or explicit higher-cost modes.

---

## 6. Generation Benchmark v1

Generation Benchmark v1 evaluates the local production-style generation path.

The final benchmark contains 12 manually designed cases across:

- semantic,
- lexical,
- ambiguous,
- version-specific,
- cross-tool,
- insufficient-evidence queries.

The evaluated local configuration is:

```text
Retriever          Weighted RRF
Dense weight       0.7
BM25 weight        0.3
RRF k              60
Top-k              10

Context sources    6
Context tokens     4000

Generator          Ollama
Model              qwen3:4b-instruct
Temperature        0.0
Output budget      384 tokens
Prompt             v3
```

### Final v3 Token Behavior

| Metric | Value |
|---|---:|
| Mean prompt tokens | 2954.25 |
| Mean completion tokens | 194.75 |
| Maximum completion tokens | 360 |

The final v3 run had no output truncation.

### Final v3 Latency

| Metric | Value |
|---|---:|
| Mean retrieval latency | 178.00 ms |
| Mean generation latency | 15,376.63 ms |
| Mean end-to-end latency | 15,554.84 ms |
| Median end-to-end latency | 17,609.48 ms |
| P95 end-to-end latency | 23,224.35 ms |

Local generation was the dominant latency component in this benchmark.

### Quality Findings

The benchmark showed strong behavior for:

- factual grounded answering,
- lexical questions,
- version-specific questions,
- cross-source synthesis,
- insufficient-evidence abstention.

Known limitations included:

- ambiguous-query handling,
- raw citation-format compliance,
- local inference latency.

Prompt tuning was stopped after v3 to avoid overfitting the same 12 development cases.

> The generation benchmark above evaluates the local Ollama profile. It should not be interpreted as a benchmark of the later Groq cloud profile.

---

## 7. End-to-End Validation v1

The frozen E2E benchmark was created separately from the 12-case generation development benchmark.

It validates the real request path:

```text
FastAPI /v1/query
   ↓
RAGService
   ↓
Retrieval
   ↓
ContextBuilder
   ↓
PromptBuilder
   ↓
Generator
   ↓
API response
```

The frozen v1 set contains 18 cases covering:

- lexical,
- semantic,
- ambiguous,
- cross-tool,
- version-specific,
- insufficient-evidence behavior.

The E2E milestone validates both structural and semantic behavior, including:

- HTTP response behavior,
- response schema,
- non-empty answers for answerable cases,
- citation/source mapping,
- evidence sufficiency,
- insufficient-evidence behavior,
- dependency error behavior,
- end-to-end latency.

Canonical decision report:

```text
benchmarks/e2e/reports/e2e_v1_decision.md
```

---

## 8. Load and Performance Characterization

The local production-style runtime was characterized using:

- warm steady-state requests,
- burst concurrency,
- fixed-periodic open-loop traffic,
- Poisson open-loop traffic,
- post-test resource and observability checks.

A representative warm C=1 run produced:

| Metric | Result |
|---|---:|
| Requests | 10 |
| Success | 10 / 10 |
| Successful throughput | 0.3038 answers/s |
| Client mean | 3291.43 ms |
| Client P95 | 3311.34 ms |
| Retrieval mean | 77.44 ms |
| Generation mean | 3209.54 ms |
| Server E2E mean | 3287.05 ms |
| Server E2E P95 | 3306.94 ms |

Generation accounted for approximately 97.6% of successful server-side latency in that local runtime.

With one generation slot, burst concurrency produced controlled `503 busy` responses rather than unbounded queue growth.

This behavior was intentional and validated as part of production hardening.

---

## 9. Cloud Retrieval Compatibility

The free-tier cloud profile uses a lower-memory retrieval runtime:

```text
FastEmbed BGE query encoder
Qdrant Cloud canonical BGE vectors
Qdrant exact BM25 sparse vectors
Weighted RRF
```

The final cloud retrieval evaluation achieved:

| Metric | Score |
|---|---:|
| Hit@1 | 0.5800 |
| Hit@3 | 0.8000 |
| Hit@5 | 0.9000 |
| Hit@10 | 0.9300 |
| Recall@10 | 0.8208 |
| nDCG@10 | 0.6677 |
| MRR | 0.7119 |

Reference local Weighted RRF MRR:

```text
0.7247
```

Cloud MRR:

```text
0.7119
```

The cloud profile therefore preserves Hit@10 while accepting a small ranking-quality reduction in exchange for much lower deployment memory.

### Exact BM25 Parity Canary

A 500-chunk parity canary over 100 query texts produced:

```text
Exact top-10 order            100 / 100
Mean top-10 local coverage    1.000000
Maximum shared score delta    0.0000024688
Mismatched queries            0
```

This validated the exact rank_bm25-compatible sparse representation before full cloud migration.

---

## 10. Deployment Characterization

The cloud-slim Docker image was validated before public deployment.

### Docker Validation

```text
Image size                 ~130.5 MB
Linux Docker warm RSS      ~260.5 MiB
```

### Hosted Render Validation

Observed public deployment:

```text
Render hosted RSS          ~317 MiB
Render memory budget       512 MiB
Observed headroom          ~195 MiB
```

Observed warm public request:

```text
Backend E2E                ~2.9 s
Client E2E                 ~3.4 s
Warm /health client        ~0.3–0.7 s
```

The deployed service also validated:

- `/health` returns 200,
- `/ready` returns 200,
- Qdrant Cloud readiness,
- Groq readiness,
- successful public `/v1/query`,
- grounded answers with citations,
- Prometheus metrics,
- API schema rejection for invalid input.

Cold-start latency is not published as a fixed v1 benchmark because the observed first-request samples contained uncontrolled transport variability.

---

## 11. Production v1 Decision

The final deterministic v1 system prioritizes:

```text
reproducibility
→ measured quality
→ predictable latency
→ grounded generation
→ controlled failure behavior
→ deployability
```

The production-default retrieval path is:

```text
Dense
  +
BM25
  ↓
Weighted RRF
  ↓
Context
  ↓
Grounded generation
```

The following are intentionally not globally enabled:

- automatic adaptive retrieval,
- automatic Multi-Query escalation,
- global cross-encoder reranking,
- autonomous LangGraph agent behavior.

These remain future or experimental capabilities rather than part of the frozen v1 production baseline.

---

## 12. Evaluation Principle

The central engineering rule used throughout the project is:

```text
baseline
→ targeted hypothesis
→ controlled experiment
→ quality measurement
→ latency measurement
→ production decision
```

The project intentionally retains negative benchmark results because they explain why the final architecture is simpler than the set of all evaluated techniques.
