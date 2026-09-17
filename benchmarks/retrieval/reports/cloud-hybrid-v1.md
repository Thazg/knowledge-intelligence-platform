# Cloud Hybrid Retrieval Evaluation v1

Re-run of the cloud deployment-profile retrieval evaluation.
Generator: `scripts/evaluate_fastembed_exact_bm25_cloud_hybrid.py`
Date: 2026-09-17.
Raw stdout: `.benchmark-results/cloud-hybrid-rerun-2026-09-17.txt` (gitignored local artifact).

## Configuration

- Cases: `benchmarks/retrieval/cases.jsonl` (100 active cases, sha256: `34A5BD7273C643A9E83D9BBC85AAB40E13439FE8ABF82BA594B3423169CC9B97`)
- Collection: `enterprise_knowledge_cloud_bge_rank_bm25_v1` (Qdrant Cloud)
- Dense: FastEmbed `BAAI/bge-small-en-v1.5` (query) + canonical BGE vectors (docs)
- Sparse: exact rank_bm25 artifact (`.benchmark-results/rank-bm25-query-artifact-v1.json`, sha256: `FCD2CA656B1A704F43AAA432216E4CA827C1DA740310C7FE2D08D14FA4BAE0E6`)
- Fusion: Weighted RRF dense=0.7 bm25=0.3 k=60, top_k=10
- Runtime: 59.48 s total, 594.76 ms mean case latency

## Overall Results

| Metric | Score |
|---|---:|
| Hit@1 | 0.5800 |
| Hit@3 | 0.8000 |
| Hit@5 | 0.9000 |
| Hit@10 | 0.9300 |
| Recall@3 | 0.6258 |
| Recall@5 | 0.7542 |
| Recall@10 | 0.8208 |
| nDCG@3 | 0.5885 |
| nDCG@5 | 0.6449 |
| nDCG@10 | 0.6677 |
| MRR | 0.7119 |

Reproduces the previously published cloud table exactly (deterministic retrieval).
Reference local Weighted RRF: Hit@10 0.9300, MRR 0.7247.

## Results by Category

| Category | Cases | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Recall@10 | nDCG@10 | MRR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ambiguous | 20 | 0.4000 | 0.5500 | 0.7000 | 0.7000 | 0.5500 | 0.4170 | 0.5100 |
| cross_tool | 20 | 0.4000 | 0.7500 | 0.9000 | 0.9500 | 0.7292 | 0.5775 | 0.6088 |
| lexical | 20 | 0.6500 | 0.9500 | 1.0000 | 1.0000 | 0.9500 | 0.8097 | 0.7958 |
| semantic | 20 | 0.7000 | 0.9000 | 0.9000 | 1.0000 | 0.9250 | 0.7153 | 0.8071 |
| version_specific | 20 | 0.7500 | 0.8500 | 1.0000 | 1.0000 | 0.9500 | 0.8191 | 0.8375 |