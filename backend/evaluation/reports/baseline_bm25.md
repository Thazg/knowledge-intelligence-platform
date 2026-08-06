# BM25 Retrieval Baseline

## Configuration

- Corpus: 33,632 fixed-token chunks
- Maximum chunks per document: 1
- Candidate multiplier: 5
- Evaluation cases: 11

## Metrics

- Hit@1: 0.3636
- Hit@3: 0.7273
- Hit@5: 0.9091
- Hit@10: 1.0000
- MRR: 0.5842

## Comparison with Dense Retrieval

| Metric | Dense | BM25 |
|---|---:|---:|
| Hit@1 | 0.5455 | 0.3636 |
| Hit@3 | 0.8182 | 0.7273 |
| Hit@5 | 0.9091 | 0.9091 |
| Hit@10 | 1.0000 | 1.0000 |
| MRR | 0.7197 | 0.5842 |

## Findings

Dense retrieval performs better overall, especially at the highest ranks. BM25 performs better on several keyword-heavy queries, including Docker cache, FastAPI validation, and LangGraph interrupts.

The complementary behavior supports combining the two retrieval methods using Reciprocal Rank Fusion.