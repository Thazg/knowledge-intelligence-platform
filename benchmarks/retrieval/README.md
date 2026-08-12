# Retrieval Benchmark

This directory contains the canonical retrieval evaluation suite for the
Enterprise Knowledge Intelligence Platform.

The benchmark is used to compare retrieval strategies, detect regressions,
and support evidence-based retrieval architecture decisions.

---

## Benchmark Goals

The retrieval benchmark evaluates:

- Retrieval accuracy
- Ranking quality
- Relevant-document coverage
- Behavior across different query types
- Reproducibility across retrieval experiments

Retrieval latency is evaluated separately.

---

## Canonical Evaluation Dataset

The canonical benchmark dataset is:

```text
benchmarks/retrieval/cases.jsonl
```

It contains:

```text
100 evaluation cases
```

distributed evenly across five categories:

```text
20 semantic
20 lexical
20 ambiguous
20 version-specific
20 cross-tool
```

Each case may contain multiple relevant documents with graded relevance.

Relevance levels:

```text
3 = highly relevant
2 = relevant
1 = partially relevant
```

---

## Evaluation Case Schema

Example:

```json
{
  "case_id": "docker_buildkit_001",
  "query": "What is Docker BuildKit and how is it used during image builds?",
  "category": "lexical",
  "status": "active",
  "relevant_documents": [
    {
      "source": "docker",
      "path": "content/manuals/build/buildkit/_index.md",
      "relevance": 3
    }
  ]
}
```

Important fields:

- `case_id`: unique evaluation-case identifier
- `query`: retrieval query
- `category`: benchmark category
- `status`: whether the case is active
- `relevant_documents`: manually verified ground-truth documents
- `relevance`: graded relevance score

---

## Evaluated Retrieval Strategies

The benchmark currently evaluates:

```text
Dense Retrieval
BM25
Weighted RRF
Multi-Query Retrieval
Cross-Encoder Reranking
```

The canonical first-stage hybrid configuration is:

```text
Dense weight = 0.7
BM25 weight  = 0.3
RRF k        = 60
```

---

## Evaluation Metrics

Retrieval quality is measured using:

```text
Hit@K
Recall@K
nDCG@K
MRR
```

### Hit@K

Measures whether at least one relevant document appears within the first
`K` retrieved results.

### Recall@K

Measures how much of the relevant-document set appears within the first
`K` results.

### nDCG@K

Measures ranking quality while considering graded relevance and result
position.

### MRR

Measures how early the first relevant document appears in the ranking.

---

## Canonical Reports

Retrieval-quality report:

```text
benchmarks/retrieval/reports/retrieval_benchmark_v1.md
```

Retrieval-latency report:

```text
benchmarks/retrieval/reports/retrieval_latency_v1.md
```

The reports intentionally have separate responsibilities:

```text
retrieval_benchmark_v1.md
    -> retrieval quality

retrieval_latency_v1.md
    -> operational latency and quality-versus-latency trade-offs
```

---

## Query Rewrites

Canonical deterministic rewrites used by Multi-Query evaluation are stored in:

```text
benchmarks/retrieval/query_rewrites.jsonl
```

Frozen rewrites are used so benchmark results remain deterministic and do not
depend on live LLM generation.

---

## Running Retrieval Evaluations

Dense Retrieval:

```powershell
python -u scripts\evaluate_dense_retrieval.py
```

BM25:

```powershell
python -u scripts\evaluate_bm25_retrieval.py
```

Weighted RRF:

```powershell
python -u scripts\evaluate_hybrid_retrieval.py
```

Multi-Query:

```powershell
python -u scripts\evaluate_multi_query_retrieval.py
```

Cross-Encoder reranking:

```powershell
python -u scripts\evaluate_reranked_retrieval.py
```

Latency benchmark:

```powershell
python -u scripts\benchmark_retrieval_latency.py
```

---

## Regression Testing

The repository contains a smaller deterministic retrieval regression suite for
CI.

Relevant files:

```text
benchmarks/retrieval/ci/cases.jsonl
benchmarks/retrieval/ci/chunks.jsonl
benchmarks/retrieval/ci/baseline.json
```

The fast regression suite is designed to detect retrieval regressions without
requiring the complete production corpus.

The full 100-case benchmark remains the canonical retrieval-quality evaluation.

---

## Full Benchmark Reproducibility

Full benchmark provenance is recorded in:

```text
benchmarks/retrieval/full/manifest.json
```

The manifest records the frozen benchmark inputs and retrieval configuration
required to reproduce the approved benchmark environment.

Canonical benchmark artifacts should not be changed casually.

Changes to:

```text
evaluation cases
ground truth
corpus
embedding model
retrieval configuration
query rewrites
```

may invalidate direct comparison with previous benchmark results.

---

## Development and Review Artifacts

The following directory is used for local benchmark inspection and manual
ground-truth review:

```text
benchmarks/retrieval/review/
```

Files in this directory are development artifacts and are not part of the
canonical benchmark contract unless explicitly promoted.

---

## Benchmark Principles

The retrieval benchmark follows several principles:

1. Use manually verified ground truth.
2. Compare retrieval strategies on the same evaluation cases.
3. Change one experimental variable at a time when possible.
4. Preserve deterministic query rewrites for reproducibility.
5. Separate retrieval quality from latency evaluation.
6. Treat small development benchmarks as screening tools rather than final
   production evidence.
7. Prefer measured results over assumptions about model or pipeline complexity.

The canonical 100-case benchmark is the source of truth for retrieval-quality
decisions.
