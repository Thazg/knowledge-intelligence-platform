# Dataset

Enterprise KIP searches a curated snapshot of **technical documentation**, not the open web or private company data. The corpus was chosen to test questions that span AI tooling, APIs, vector search, containers, and orchestration. It is primarily English-language documentation copied from the projects' public repositories. Answers should be interpreted against this indexed snapshot, which can lag behind upstream documentation.

## What is in the corpus?

The table describes the **frozen v1 corpus** in `data/processed/chunks_fixed.jsonl`, counting the `src/oss/langgraph/` subtree as LangGraph rather than LangChain. Counts were checked against the local JSONL files; the chunk file's SHA-256 matches the [retrieval manifest](../benchmarks/retrieval/full/manifest.json). A document is an accepted source file; a chunk is a segment of that document used for retrieval. This table changes only how the existing files are counted; it does not change their stored `source` labels.

| Source grouping | Upstream repository | Paths in the frozen corpus | Documents | Chunks |
| --- | --- | --- | ---: | ---: |
| Docker | [docker/docs](https://github.com/docker/docs) | Repository root | 943 | 7,170 |
| FastAPI | [fastapi/fastapi](https://github.com/fastapi/fastapi) | `docs` | 152 | 761 |
| Hugging Face Transformers | [huggingface/transformers](https://github.com/huggingface/transformers) | `docs` | 731 | 4,783 |
| Kubernetes | [kubernetes/website](https://github.com/kubernetes/website) | Repository root | 1,374 | 13,495 |
| LangChain | [langchain-ai/docs](https://github.com/langchain-ai/docs) | `src/oss`, excluding `langgraph/` | 650 | 6,373 |
| LangGraph | [langchain-ai/docs](https://github.com/langchain-ai/docs) | `src/oss/langgraph/` plus legacy `src/langgraph/llms.txt` | 42 | 1,023 |
| Qdrant | [qdrant/landing_page](https://github.com/qdrant/landing_page) | `qdrant-landing/content/documentation` | 720 | 2,594 |
| **Total** | | | **4,612** | **36,199** |

The v1 ingestion configuration copied `src/oss` under the `langchain` label and the old `src/langgraph` path under `langgraph`. As a result, **41 LangGraph documents / 1,021 chunks** from `src/oss/langgraph/` are stored with the `langchain` label. The stored v1 labels remain LangChain **691 / 7,394** and LangGraph **1 / 2**; the table attributes those 41 documents to LangGraph, yielding **650 / 6,373** and **42 / 1,023**. The LangChain row is the remaining `src/oss` material, which can include shared documentation outside `src/oss/langchain/`. No JSONL records, IDs, Qdrant index, or benchmark cases are changed. The processed corpus contains 3,913 Markdown, 690 MDX, 8 HTML, and 1 plain-text documents. The discovery code supports RST too, but no RST document survived into this snapshot.

**Coverage is uneven.** LangGraph has 42 documents in this snapshot when counted by path, but only one is labelled `langgraph` in the stored v1 records. Kubernetes contributes the most chunks, so this is not a balanced sample across technologies.

## Why these sources?

The selected repositories contain first-party developer documentation for tools that AI and platform engineers often use together. Their different structures and formats make them useful for testing ingestion, hybrid retrieval, citations, and questions that combine multiple tools. The corpus is deliberately bounded: it does not index arbitrary websites, company knowledge, current pricing, live security advisories, or every version of each product.

## How the files are built

The pipeline is:

```text
public documentation repositories
  -> data/raw/<source>/
  -> discovery, filtering, parsing, normalization, metadata, quality checks
  -> data/processed/documents.jsonl
  -> BGE tokenization -> data/processed/documents_tokenized.jsonl
  -> 384-token chunks with 64-token overlap
  -> data/processed/chunks_fixed.jsonl
  -> local Qdrant dense index and BM25 retrieval
```

The ingestion step accepts `.md`, `.mdx`, `.rst`, `.html`, and `.txt` files. It excludes known repository/build noise and recognized translation directories, then rejects empty or very short documents and other low-quality inputs. The selection rules are implemented in [`backend/ingestion/`](../backend/ingestion/README.md). Tokenization and chunking use `BAAI/bge-small-en-v1.5`.

Each document record includes a source label, filename, relative path, title, headings, text, and word/token counts. Each chunk retains its document ID, source, relative path, title, chunk index, text, and token count. IDs connect retrieved chunks back to the accepted documents. The current records do **not** carry a canonical public page URL or a reliable product-version field; a citation may therefore lack a direct link, and version-sensitive answers require care. Some source-format text, such as Markdown front matter, can remain in excerpts.

From the repository root, the current pipeline can be run with:

```bash
python scripts/fetch_documents.py
python scripts/extract_metadata.py
python scripts/tokenize_documents.py
python scripts/chunk_documents.py
```

This fetch command takes the repositories' current heads, so a fresh run can produce a **different** corpus. The frozen v1 benchmark instead identifies its 36,199-chunk corpus by size and SHA-256 in [`benchmarks/retrieval/full/manifest.json`](../benchmarks/retrieval/full/manifest.json); its snapshot and corpus assets are named there. The raw and processed files under `data/` are ignored by Git to keep the repository small. Upstream documentation remains subject to each source project's own license and terms.

## Corpus versus evaluation data

The 4,612 documents are the **search corpus**, not labelled training examples. The separate [retrieval benchmark](../benchmarks/retrieval/README.md) has 100 manually verified queries across semantic, lexical, ambiguous, version-specific, and cross-tool categories. The [E2E benchmark](../benchmarks/e2e/v1/manifest.json) has 18 cases for the full answer path. Their results measure behavior on selected questions; they do not guarantee that every question about these seven sources can be answered correctly.

For source-selection rationale and ingestion challenges, see [`docs/02_dataset_analysis.md`](../docs/02_dataset_analysis.md).
