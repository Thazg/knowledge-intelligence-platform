# Enterprise Knowledge Intelligence Platform

A production-grade AI platform for ingesting, searching, retrieving, and reasoning over technical documentation across AI and software engineering ecosystems.

The project currently focuses on the document ingestion layer: fetching documentation repositories, discovering raw files, parsing supported formats, normalizing content, extracting metadata, filtering low-quality records, and writing a JSONL corpus for downstream chunking and retrieval.

## Project Goals

- Build a production-grade Retrieval-Augmented Generation (RAG) platform.
- Support multiple technical documentation sources.
- Provide reliable answers with citations.
- Demonstrate AI Engineering and MLOps best practices.

## Current Data Sources

- LangChain
- LangGraph
- FastAPI
- Docker
- Kubernetes
- Hugging Face Transformers
- Qdrant

## Roadmap

- [x] Project Planning
- [ ] System Architecture
- [x] Document Ingestion
- [x] Metadata Extraction
- [ ] Chunking
- [ ] Embedding Benchmark
- [ ] Hybrid Retrieval
- [ ] Reranking
- [ ] LangGraph Agent
- [ ] Evaluation
- [ ] Monitoring
- [ ] Authentication
- [ ] Docker
- [ ] Kubernetes
- [ ] CI/CD
- [ ] Deployment

## Project Structure

```text
knowledge-intelligence-platform/
|-- backend/
|   |-- chunking/
|   |-- ingestion/
|   `-- tokenization/
|-- benchmarks/
|-- data/
|   |-- raw/
|   |-- processed/
|   `-- temp/
|-- deployment/
|-- docker/
|-- docs/
|-- frontend/
|-- kubernetes/
|-- scripts/
`-- README.md
```

## Ingestion Commands

```bash
python scripts/fetch_documents.py
python scripts/discover_documents.py
python scripts/extract_metadata.py
python scripts/test_serializer.py
python scripts/tokenize_documents.py
python scripts/test_fixed_token_chunker.py
```
