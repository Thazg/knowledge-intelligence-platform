# Ingestion Component

## Responsibility

Build a normalized JSONL documentation corpus from source repositories.

## Pipeline

1. Fetch configured documentation repositories into `data/raw/`.
2. Discover supported document files.
3. Filter repository metadata, build artifacts, generated content, and non-English translations.
4. Parse Markdown/MDX, HTML, RST, and plain text into normalized text content.
5. Extract metadata such as title, headings, and word count.
6. Apply quality filters.
7. Write accepted records to `data/processed/documents.jsonl`.

## Supported Formats

- `.md`
- `.mdx`
- `.rst`
- `.html`
- `.txt`

## Notes

`token_count` is populated by the tokenization stage before downstream chunking and retrieval.
