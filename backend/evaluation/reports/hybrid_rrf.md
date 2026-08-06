# Hybrid Retrieval Evaluation with Reciprocal Rank Fusion

## 1. Overview

This report evaluates a hybrid retrieval pipeline that combines:

- dense vector retrieval;
- BM25 lexical retrieval;
- Reciprocal Rank Fusion (RRF);
- document-level deduplication.

The objective is to determine whether hybrid retrieval improves ranking quality and retrieval coverage compared with using dense retrieval or BM25 independently.

---

## 2. Evaluation Setup

### 2.1 Corpus

- Total chunks: 33,632
- Chunking strategy: fixed-token chunking
- Chunk size: 384 tokens
- Chunk overlap: 64 tokens

### 2.2 Dense Retrieval

- Embedding model: `BAAI/bge-small-en-v1.5`
- Vector database: Qdrant
- Similarity metric: cosine similarity

### 2.3 Sparse Retrieval

- Retrieval algorithm: BM25
- Implementation: `rank-bm25`

### 2.4 Result Diversification

- Maximum chunks per document: 1
- Candidate multiplier: 5

Each retriever returns a larger candidate pool before fusion. After ranking, at most one chunk from each document is kept in the final result set.

### 2.5 Evaluation Dataset

- Evaluation cases: 11
- Ground truth: one expected document per query

The following metrics are reported:

- Hit@1
- Hit@3
- Hit@5
- Hit@10
- Mean Reciprocal Rank (MRR)

Because each query currently has one expected document, Hit@K is equivalent to Recall@K for this evaluation dataset.

---

## 3. Dense Retrieval Baseline

Dense retrieval produced the strongest standalone baseline.

| Metric | Dense Retrieval |
|---|---:|
| Hit@1 | 0.5455 |
| Hit@3 | 0.8182 |
| Hit@5 | 0.9091 |
| Hit@10 | 1.0000 |
| MRR | 0.7197 |

Dense retrieval performed especially well for queries where semantic meaning was more important than exact keyword overlap.

---

## 4. BM25 Baseline

BM25 provided a lexical retrieval baseline based on exact-term matching.

| Metric | BM25 |
|---|---:|
| Hit@1 | 0.3636 |
| Hit@3 | 0.7273 |
| Hit@5 | 0.9091 |
| Hit@10 | 1.0000 |
| MRR | 0.5842 |

BM25 performed worse than dense retrieval overall, but it ranked several keyword-heavy queries more effectively.

This indicates that BM25 and dense retrieval provide complementary retrieval signals.

---

## 5. Equal-Weight RRF Experiment

### 5.1 Configuration

- Fusion method: Reciprocal Rank Fusion
- RRF constant: 60
- Dense weight: 1.0
- BM25 weight: 1.0

The fusion score is calculated as:

```text
RRF score =
    1 / (k + dense_rank)
    +
    1 / (k + bm25_rank)
```

where:

```text
k = 60
```

### 5.2 Results

| Metric | Dense | BM25 | Equal-Weight RRF |
|---|---:|---:|---:|
| Hit@1 | 0.5455 | 0.3636 | 0.3636 |
| Hit@3 | 0.8182 | 0.7273 | 0.8182 |
| Hit@5 | 0.9091 | 0.9091 | 1.0000 |
| Hit@10 | 1.0000 | 1.0000 | 1.0000 |
| MRR | 0.7197 | 0.5842 | 0.6318 |

### 5.3 Findings

Equal-weight RRF improved Hit@5 from `0.9091` to `1.0000`.

This confirms that dense retrieval and BM25 contribute complementary candidates.

However, ranking quality at the highest positions decreased:

- Hit@1 decreased from `0.5455` to `0.3636`;
- MRR decreased from `0.7197` to `0.6318`.

Dense retrieval performed better than BM25 on the evaluation dataset. Giving both retrievers equal influence allowed lower-quality BM25 rankings to push some relevant dense results downward.

Equal-weight RRF therefore improved coverage but reduced early-rank precision.

---

## 6. Weighted RRF Experiment

### 6.1 Configuration

- Fusion method: Weighted Reciprocal Rank Fusion
- RRF constant: 60
- Dense weight: 0.7
- BM25 weight: 0.3
- Candidate multiplier: 5
- Maximum chunks per document: 1

The weighted fusion score is calculated as:

```text
Weighted RRF score =
    0.7 / (k + dense_rank)
    +
    0.3 / (k + bm25_rank)
```

where:

```text
k = 60
```

### 6.2 Results

| Metric | Dense | BM25 | Equal-Weight RRF | Weighted RRF |
|---|---:|---:|---:|---:|
| Hit@1 | 0.5455 | 0.3636 | 0.3636 | 0.5455 |
| Hit@3 | 0.8182 | 0.7273 | 0.8182 | 0.9091 |
| Hit@5 | 0.9091 | 0.9091 | 1.0000 | 1.0000 |
| Hit@10 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| MRR | 0.7197 | 0.5842 | 0.6318 | 0.7303 |

### 6.3 Findings

Weighted RRF produced the strongest overall result.

Compared with the dense baseline:

- Hit@1 remained unchanged at `0.5455`;
- Hit@3 improved from `0.8182` to `0.9091`;
- Hit@5 improved from `0.9091` to `1.0000`;
- Hit@10 remained unchanged at `1.0000`;
- MRR improved from `0.7197` to `0.7303`.

Giving dense retrieval more influence preserved its semantic ranking quality, while BM25 contributed useful exact-term matches that improved candidate coverage.

Weighted RRF also outperformed equal-weight RRF across all early-ranking metrics.

---

## 7. Overall Comparison

| Metric | Dense | BM25 | Equal-Weight RRF | Weighted RRF |
|---|---:|---:|---:|---:|
| Hit@1 | 0.5455 | 0.3636 | 0.3636 | **0.5455** |
| Hit@3 | 0.8182 | 0.7273 | 0.8182 | **0.9091** |
| Hit@5 | 0.9091 | 0.9091 | 1.0000 | **1.0000** |
| Hit@10 | 1.0000 | 1.0000 | 1.0000 | **1.0000** |
| MRR | 0.7197 | 0.5842 | 0.6318 | **0.7303** |

The experiments show that:

1. Dense retrieval is the strongest standalone retriever.
2. BM25 adds useful lexical evidence for keyword-heavy queries.
3. Equal-weight RRF improves coverage but gives too much influence to BM25.
4. Weighted RRF preserves dense retrieval quality while benefiting from BM25 candidate coverage.
5. Document-level deduplication prevents repeated chunks from the same document from occupying the final Top-K results.

---

## 8. Selected Default Configuration

The following configuration is selected as the current default hybrid retrieval baseline:

```text
Fusion method: Weighted Reciprocal Rank Fusion
RRF constant: 60
Dense weight: 0.7
BM25 weight: 0.3
Candidate multiplier: 5
Maximum chunks per document: 1
```

This configuration achieved:

```text
Hit@1  = 0.5455
Hit@3  = 0.9091
Hit@5  = 1.0000
Hit@10 = 1.0000
MRR    = 0.7303
```

---

## 9. Conclusion

Weighted RRF currently provides the best retrieval performance in the system.

It preserves the strong semantic ranking of dense retrieval while using BM25 to improve lexical coverage. The result is better Hit@3, Hit@5, and MRR than either standalone retriever.

Weighted RRF should therefore be used as the current default candidate-retrieval strategy.

The next retrieval improvement should apply a cross-encoder reranker to the top hybrid candidates and measure whether it improves Hit@1 and MRR further.

---

## 10. Limitations

The current benchmark contains only 11 evaluation cases. It is sufficient for an initial comparison, but it does not yet represent the full range of queries supported by the corpus.

Future evaluation should include:

- more queries from every documentation source;
- definition, comparison, configuration, troubleshooting, and how-to queries;
- multiple relevant documents per query;
- graded relevance judgments;
- nDCG evaluation;
- latency measurements;
- memory usage measurements;
- experiments with different RRF constants and retrieval weights;
- evaluation of cross-encoder reranking.