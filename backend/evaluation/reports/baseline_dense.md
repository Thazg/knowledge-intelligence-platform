# Dense Retrieval Baseline

## Failure Case: Docker BuildKit

### Query

Explain Docker BuildKit and how it differs from the legacy builder.

### Expected document

`content/manuals/build/buildkit/_index.md`

### Initial result

Dense retrieval returned Docker release notes instead of the BuildKit overview page.

### Root cause

The `build` directory name was included in the ignored-directory rules of both:

- `DocumentDiscovery`
- `DocumentFilter`

This unintentionally excluded valid documentation under:

`content/manuals/build/`

### Resolution

Removed `build` from the ignored-directory lists, reran ingestion, tokenization, chunking, and Qdrant indexing.

### Failure category

Ingestion coverage gap caused by an overly broad path-exclusion rule.

### Lesson learned

Generic directory names such as `build` can represent generated artifacts in one repository and legitimate documentation categories in another. Exclusion rules should be source-aware or narrowly scoped.

## Document Deduplication Experiment

Configuration:

- Candidate multiplier: 5
- Maximum chunks per document: 1
- Evaluation cases: 11

### Before deduplication

- Hit@1: 0.5455
- Hit@3: 0.8182
- Hit@5: 0.9091
- Hit@10: 1.0000
- MRR: 0.7152

### After deduplication

- Hit@1: 0.5455
- Hit@3: 0.8182
- Hit@5: 0.9091
- Hit@10: 1.0000
- MRR: 0.7197

### Conclusion

Document-level deduplication preserved retrieval recall while slightly improving MRR. It also increased result diversity by preventing multiple chunks from the same document from occupying the Top-K results.