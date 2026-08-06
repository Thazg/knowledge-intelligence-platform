# Dataset Analysis

## 1. Data Sources

| Source | Primary Format | Ingestion Path |
| :--- | :--- | :--- |
| LangChain | Markdown / MDX | `src/oss` |
| LangGraph | Markdown / MDX | `src/langgraph` |
| FastAPI | Markdown | `docs/en/docs` |
| Docker | Markdown / HTML | `content` |
| Kubernetes | Markdown / HTML | `content/en/docs` |
| Hugging Face Transformers | Markdown / MDX / RST | `docs/source/en` |
| Qdrant | Markdown | `docs` |

## 2. Selection Rationale

These are official developer documentation sources representing core technologies in AI engineering and software infrastructure. They are version-controlled, structurally rich, and large enough to stress realistic ingestion, metadata extraction, filtering, chunking, and retrieval workflows.

## 3. Common Characteristics

- **Language:** The ingestion configuration targets English documentation where the upstream repository separates translations by path.
- **Structure:** Documents commonly include headings, lists, tables, admonitions, code blocks, and front matter.
- **Source Control:** The raw corpus is fetched from public Git repositories, which makes refreshes reproducible.

## 4. Technical Challenges

- **Repository Noise:** Documentation repositories also contain templates, build scripts, static assets, generated files, and contribution metadata that should not enter the retrieval corpus.
- **Format Variance:** Markdown, MDX, RST, and HTML expose metadata differently and need format-aware parsing.
- **Translation Layouts:** Some repositories keep many languages under the same docs root, so ingestion must select English content consistently.
- **Code Block Density:** Technical docs include many code snippets whose context must be preserved for later chunking and retrieval.

## 5. Objectives of the Ingestion Step

The ingestion step transforms raw documentation repositories into a unified JSONL corpus. Each record should include source metadata, relative path, normalized text content, extracted title, headings, and word count. Token counting is intentionally left as a later tokenizer/chunking task.
