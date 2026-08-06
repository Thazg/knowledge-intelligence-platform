# Hybrid RRF Retrieval Evaluation

## Configuration

- Dense retriever: BAAI/bge-small-en-v1.5
- Sparse retriever: BM25
- Fusion: Reciprocal Rank Fusion
- RRF k: 60
- Candidate multiplier: 5
- Maximum chunks per document: 1
- Evaluation cases: 11

## Metrics

| Metric | Dense | BM25 | Hybrid RRF |
|---|---:|---:|---:|
| Hit@1 | 0.5455 | 0.3636 | 0.3636 |
| Hit@3 | 0.8182 | 0.7273 | 0.8182 |
| Hit@5 | 0.9091 | 0.9091 | 1.0000 |
| Hit@10 | 1.0000 | 1.0000 | 1.0000 |
| MRR | 0.7197 | 0.5842 | 0.6318 |

## Findings

Hybrid RRF improved Hit@5 from 0.9091 to 1.0000, showing that dense and
BM25 retrieval provide complementary candidates.

However, Hit@1 and MRR were lower than dense retrieval. Equal-weight RRF
gave too much influence to BM25, which performed worse than dense retrieval
on this evaluation set.

## Conclusion

The current hybrid configuration improves recall but should not replace
dense retrieval as the default ranking strategy yet. Weighted fusion or a
reranker should be evaluated next.